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
        coupon_count = expired_coupons.count()
        logger.info(f"Found {coupon_count} expired coupons.")

        if coupon_count > 0:
            expired_coupons.update(is_active=False)
            logger.info(f"Successfully deactivated {coupon_count} expired coupons.")
        else:
            logger.debug("No expired coupons found during this check.")
    except Exception as error:
        logger.error(f"Error in check_coupon_expiration task: {error}", exc_info=True)
      

#======================================================================================================== 
