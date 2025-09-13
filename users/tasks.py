from celery import shared_task
from django.utils.timezone import now, localtime
from django.core.cache import cache
import logging
import time
from .models import *
from config.storages import Bucket


# Start the Celery worker
# on Windows: celery -A config.celery_config worker --pool=solo --loglevel=info
# on Linux:   celery -A config.celery_config worker --loglevel=info
# on Linux:   celery -A config.celery_config worker --pool=solo --loglevel=info -B

# Start Celery beat
# celery -A config.celery_config beat --loglevel=info


#==================================== UpdateSubscription Celery =========================================

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("user-task")


@shared_task(rate_limit="10/m") 
def check_premium_subscriptions():
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
            logger.info(f"Deleted subscription: {sub}")

        duration = time.time() - start_time
        logger.info(f"Premium subscription check completed in {duration:.2f} seconds")

    except Exception as error:
        logger.error(f"Error in check_premium_subscriptions: {error}", exc_info=True)
      

#==================================== ArvanCloud Celery =================================================

@shared_task(bind=True, max_retries=3)
def fetch_all_files(self):
    try:
        bucket = Bucket()
        return bucket.get_files()
    except Exception as error:
        logger.error(f"Failed to fetch files: {error}")
        self.retry(exc=error, countdown=60)
        
        
@shared_task(bind=True, max_retries=3)  
def remove_file(self, key):
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
    try:
        bucket = Bucket()
        path = bucket.download_file(key, local_path)
        logger.info(f"Downloaded {key} to {path}")
        return path
    except Exception as error:
        logger.error(f"Failed to download {key}: {error}")
        self.retry(exc=error, countdown=45)


#========================================================================================================

# @shared_task
# def check_premium_subscriptions():
#     try:
#         current_date = localtime(now())
#         logger.debug(f"Checking for expired subscriptions at {current_date}")

#         expired_subscriptions = PremiumSubscription.objects.filter(expiry_date__lt=current_date)
#         logger.info(f"Expired subscriptions: {expired_subscriptions}")

#         for sub in expired_subscriptions:
#             logger.debug(f"Processing subscription: {sub}")
#             user = sub.user
#             user.is_premium = False
#             user.save()

#             # Update Redis cache
#             cache_key = f"user_{user.id}_is_premium"
#             cache.set(cache_key, False, timeout=3600) 
#             logger.info(f"Cached {cache_key} = False")

#             sub.delete()
#             logger.info(f"Deleted subscription: {sub}")

#         logger.info(f"Checked premium subscriptions at {current_date}")

#     except Exception as error:
#         logger.error(f"Error in check_premium_subscriptions: {error}")


# is_premium = cache.get("user_42_is_premium")