from celery import shared_task
from django.utils.timezone import now, localtime
import logging
from .models import *


# Start the Celery worker
# on Windows: celery -A config.celery_config worker --pool=solo --loglevel=info
# on Linux:   celery -A config.celery_config worker --loglevel=info
# on Linux:   celery -A config.celery_config worker --pool=solo --loglevel=info -B

# Start Celery beat
# celery -A config.celery_config beat --loglevel=info


#==================================== UpdateCoupon Celery =========================================

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("user-task")

@shared_task
def check_coupon_expiration():
    try:
        current_date = localtime(now())
        logger.debug(f"Starting coupon expiration check at {current_date}.")

        expired_coupons = Coupon.objects.filter(valid_to__lt=current_date, is_active=True)
        expired_count = expired_coupons.count()
        logger.info(f"Found {expired_count} expired coupons.")

        if expired_count > 0:
            expired_coupons.update(is_active=False)
            logger.info(f"Successfully deactivated {expired_count} expired coupons.")

        max_usage_coupons = Coupon.objects.filter(usage_count__gte=models.F("max_usage"), is_active=True)
        max_usage_count = max_usage_coupons.count()
        logger.info(f"Found {max_usage_count} coupons that have reached their maximum usage.")

        if max_usage_count > 0:
            max_usage_coupons.update(is_active=False)
            logger.info(f"Successfully deactivated {max_usage_count} coupons due to maximum usage.")

        if expired_count == 0 and max_usage_count == 0:
            logger.debug("No expired or max usage coupons found during this check.")

    except Exception as error:
        logger.error(f"Error in check_coupon_expiration task: {error}", exc_info=True)


#==================================================================================================