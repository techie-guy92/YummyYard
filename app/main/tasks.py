from celery import shared_task
from django.utils.timezone import now, localtime
from django.core.cache import cache
import logging
import time
from django.db import models
from .models import *


# Start the Celery worker
# celery -A config.celery_config worker --loglevel=info
# celery -A config.celery_config worker --pool=solo --loglevel=info
# celery -A config.celery_config worker --pool=solo --loglevel=info -B

# Start Celery beat
# celery -A config.celery_config beat --loglevel=info


#==================================== UpdateCoupon Celery =========================================

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("user-task")


@shared_task(rate_limit="10/m")  
def check_coupon_expiration():
    start_time = time.time()
    current_date = localtime(now())
    logger.debug(f"Starting coupon expiration check at {current_date}")

    try:
        expired_coupons = Coupon.objects.filter(valid_to__lt=current_date, is_active=True)
        expired_count = expired_coupons.count()
        logger.info(f"Found {expired_count} expired coupons")

        if expired_count > 0:
            expired_coupons.update(is_active=False)
            logger.info(f"Deactivated {expired_count} expired coupons")
                                                    
        max_usage_coupons = Coupon.objects.filter(usage_count__gte=models.F("max_usage"), is_active=True)
        max_usage_count = max_usage_coupons.count()
        logger.info(f"Found {max_usage_count} coupons at max usage")

        if max_usage_count > 0:
            max_usage_coupons.update(is_active=False)
            logger.info(f"Deactivated {max_usage_count} coupons due to max usage")

        if expired_count == 0 and max_usage_count == 0:
            logger.debug("No expired or max usage coupons found")

        duration = time.time() - start_time
        logger.info(f"Coupon expiration check completed in {duration:.2f} seconds")

    except Exception as error:
        logger.error(f"Error in check_coupon_expiration task: {error}", exc_info=True)


#==================================================================================================