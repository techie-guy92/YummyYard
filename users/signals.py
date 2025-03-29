from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.timezone import now, localtime
from logging import getLogger
from .models import *
from utilities import *


#==================================== UpdateSubscription Signal =========================================

logger = getLogger("users-signal")


@receiver(post_save, sender=Payment)
def update_subscription(sender, instance, **kwargs):
    """
    Signal receiver to update the user's subscription status upon successful payment.

    Parameters:
    sender (Model): The model class that sent the signal
    instance (Payment): The instance of the model that was saved
    kwargs (dict): Additional keyword arguments

    Logs the payment processing and updates the user's subscription.
    """
    
    if instance.is_sucessful:
        instance.process_payment()
        logger.info(f"Processed payment for user: {instance.user.username}")


@receiver(post_save, sender=PremiumSubscription)
def check_subscription_expiration(sender, instance, **kwargs):
    """
    Signal receiver to check if a premium subscription has expired.

    Parameters:
    sender (Model): The model class that sent the signal
    instance (PremiumSubscription): The instance of the model that was saved
    kwargs (dict): Additional keyword arguments

    Logs the expiration status and updates the user's premium status accordingly.
    """
    
    try:
        logger.debug(f"Signal triggered for sub: {instance}\tCurrent time: {localtime(now())}\tExpiry: {instance.expiry_date}")

        if instance.is_expired():
            logger.info(f"Subscription expired: {instance}")
            user = instance.user
            user.is_premium = False
            user.save()
            logger.info(f"Updated user: {user.username} is_premium: {user.is_premium}")
        else:
            logger.info(f"Subscription not expired: {instance.expiry_date} >= {localtime(now())}")
            
    except Exception as error:
        logger.error(f"Error in check_subscription_expiration: {error}")


#========================================================================================================