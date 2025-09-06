from celery import shared_task
from django.core.cache import cache
from django.utils.timezone import now, localtime
import logging
from .models import *


# Start the Celery worker
# on Windows: celery -A config.celery_config worker --pool=solo --loglevel=info
# on Linux:   celery -A config.celery_config worker --loglevel=info
# on Linux:   celery -A config.celery_config worker --pool=solo --loglevel=info -B

# Start Celery beat
# celery -A config.celery_config beat --loglevel=info


#==================================== UpdateSubscription Celery =========================================

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("user-task")


@shared_task
def check_premium_subscriptions():
    """
    Celery task to check for expired premium subscriptions and update user status.

    Logs the process and updates users' premium status accordingly.
    """
    
    try:
        current_date = localtime(now())
        logger.debug(f"Checking for expired subscriptions at {current_date}")
        expired_subscriptions = PremiumSubscription.objects.filter(expiry_date__lt=current_date)
        logger.info(f"Expired subscriptions: {expired_subscriptions}")
        
        for sub in expired_subscriptions:
            logger.debug(f"Processing subscription: {sub}")
            user = sub.user
            user.is_premium = False
            user.save()
            logger.info(f"Updated user: {user.username} is_premium: {user.is_premium}")
            sub.delete()
            logger.info(f"Deleted subscription: {sub}")
        logger.info(f"Checked premium subscriptions at {current_date}")
      
    except Exception as error:
      print(f"Error in check_premium_subscriptions: {error}")
      

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