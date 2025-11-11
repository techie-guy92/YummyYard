from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.utils.timezone import now, localtime
from logging import getLogger
from .models import *
from utilities import *


#==================================== Update Subscription Signal ========================================

logger = getLogger(__name__)


@receiver(post_save, sender=Payment)
def process_payment(sender, instance, created, **kwargs):
    current_date = localtime(now())
    extended_date = current_date + timedelta(days=90)
    if created and instance.is_paid:
        with transaction.atomic():
            instance.user.is_premium = True
            premium_sub, created = PremiumSubscription.objects.get_or_create(user=instance.user, defaults={
                "start_date": current_date,
                "expiry_date": extended_date,
                "is_active": True
            })
            
            if not created:
                premium_sub.start_date = current_date
                premium_sub.expiry_date = extended_date
                premium_sub.is_active = True
            instance.user.save()
            premium_sub.save()
            logger.info(f"Processed payment for user: {instance.user.username}")
    else:
        logger.info(f"User has already activated: {instance.user.username}")


#========================================================================================================