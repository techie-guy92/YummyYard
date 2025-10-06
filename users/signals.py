from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.utils.timezone import now, localtime
from logging import getLogger
from .models import *
from utilities import *


#==================================== Update Subscription Signal ========================================

logger = getLogger(__name__)


@receiver(post_save, sender=Payment)
def update_subscription(sender, instance, **kwargs):
    """
    Signal receiver to update the user's subscription status upon successful payment.
    """
    if instance.is_sucessful:
        instance.process_payment()
        logger.info(f"Processed payment for user: {instance.user.username}")


# @receiver(post_delete, sender=PremiumSubscription)
# def inform_subscription(sender, instance, **kwargs):
#     user = instance.user
#     if not user.is_premium:
#         print(f"{user} is deleted")  

    
#========================================================================================================