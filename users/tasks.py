from celery import shared_task
from django.utils.timezone import now, localtime
from django.core.cache import cache
import logging
import time
from .models import *
from config.storages import Bucket


# Start the Celery worker
# on Windows: celery -A config worker --pool=solo --loglevel=info
# on Linux:   celery -A config worker --loglevel=info
# on Linux:   celery -A config worker --pool=solo --loglevel=info -B

# Start Celery beat
# celery -A config beat --loglevel=info


#==================================== Update Subscription Celery ========================================

logger = logging.getLogger(__name__)


@shared_task(rate_limit="10/m")
def check_premium_subscriptions():
    """
    Periodic Celery task to audit and clean up expired premium subscriptions.
    This task scans the PremiumSubscription model for entries whose `expiry_date` has passed.
    For each expired subscription:
        - The associated user's `is_premium` flag is set to False.
        - The subscription record is deleted.
        - Actions are logged for audit and visibility.
    The task is rate-limited to 10 executions per minute to prevent overload or accidental flooding.
    Execution time is measured and logged for performance monitoring.
    """
    start_time = time.time()
    current_date = localtime(now())
    logger.debug(f"Checking for expired subscriptions at {current_date}")
    try:
        expired_subscriptions = PremiumSubscription.objects.filter(expiry_date__lt=current_date)
        logger.info(f"Expired subscriptions: {expired_subscriptions}")
        for sub in expired_subscriptions:
            user = sub.user
            user.is_premium = False
            user.save()
            logger.info(f"Updated user: {user.username} is_premium: {user.is_premium}")
            sub.delete()
            logger.info(f"Deleted subscription for user: {user.username}")
        duration = time.time() - start_time
        logger.info(f"Premium subscription check completed in {duration:.2f} seconds")
    except Exception as error:
        logger.error(f"Error in check_premium_subscriptions: {error}", exc_info=True)
      

#==================================== ArvanCloud Celery =================================================

@shared_task(bind=True, max_retries=3)
def fetch_all_files(self):
    """
    Celery task to retrieve all files from the configured bucket.
    This task initializes a `Bucket` instance and calls its `get_files()` method to fetch file metadata.
    It logs the number of files retrieved and inspects the first three entries for debugging and visibility.
    Retries:
        - Automatically retries up to 3 times on failure.
        - Waits 60 seconds between retries.
    Returns:
        List of file metadata dictionaries, or retries on failure.
    """
    try:
        logger.info("fetch_all_files task started")
        bucket = Bucket()
        logger.info("Bucket instance created")
        
        files = bucket.get_files()
        logger.info(f"Fetched {len(files)} files from bucket")
        
        if files:
            for i, file_info in enumerate(files[:3]):  
                logger.info(f"File {i}: {file_info}")
                for key, value in file_info.items():
                    logger.info(f"  {key}: {value} (type: {type(value)})")
        return files
    except Exception as error:
        logger.error(f"Failed to fetch files: {error}", exc_info=True)
        self.retry(exc=error, countdown=60)


@shared_task(bind=True, max_retries=3)
def remove_file(self, key):
    """
    Celery task to delete a file from the bucket by its key.
    This task initializes a `Bucket` instance and calls `delete_file(key)` to remove the specified object.
    It logs the deletion result and retries on failure.
    Parameters:
        key (str): The unique identifier of the file to delete.
    Retries:
        - Automatically retries up to 3 times on failure.
        - Waits 30 seconds between retries.
    Returns:
        Result of the deletion operation, or retries on failure.
    """
    try:
        bucket = Bucket()
        result = bucket.delete_file(key)
        logger.info(f"Deleted file: {key}")
        return result
    except Exception as error:
        logger.error(f"Failed to delete {key}: {error}")
        self.retry(exc=error, countdown=30)


@shared_task(bind=True, max_retries=3)
def download_obj(self, key, local_path=None):
    """
    Celery task to download a file from the bucket to a local path.
    This task initializes a `Bucket` instance and calls `download_file(key, local_path)` to retrieve the object.
    It logs the download result and retries on failure.
    Parameters:
        key (str): The unique identifier of the file to download.
        local_path (str, optional): Destination path for the downloaded file. If not provided, a default path is used.
    Retries:
        - Automatically retries up to 3 times on failure.
        - Waits 45 seconds between retries.
    Returns:
        Path to the downloaded file, or retries on failure.
    """
    try:
        bucket = Bucket()
        path = bucket.download_file(key, local_path)
        logger.info(f"Downloaded {key} to {path}")
        return path
    except Exception as error:
        logger.error(f"Failed to download {key}: {error}")
        self.retry(exc=error, countdown=45)


#========================================================================================================