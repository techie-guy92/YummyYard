from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.utils.timezone import now, localtime
from logging import getLogger
from .models import *
from utilities import *
from custome_exception import CustomEmailException


#==================================== Update Subscription Signal ========================================

logger = getLogger(__name__)


def send_extend_premium_account(user):
    try:
        verification_link = f"http://{settings.FRONTEND_DOMAIN}"
        subject = "پایان اشتکراک ویژه"
        message = "اشتراک ویژه شما به اتمام رسید در صورت تمدید اشتراک خود روی لینک زیر کلیک کنید"
        html_content = f"""<p>درود<br>{user.first_name} {user.last_name} عزیز,
        <br><br>اشتراک ویژه شما به اتمام رسید در صورت تمدید اشتراک خود روی لینک زیر کلیک کنید:
        <br><a href="{verification_link}">تمدید اشتراک</a><br><br>ممنون</p>"""
        email_sender(subject, message, html_content, [user.email])
    except Exception as error:
        logger.error(f"Failed to send verification email: {error}")
        raise CustomEmailException("Email failed to send")
    

@receiver(post_save, sender=Payment)
def update_subscription(sender, instance, **kwargs):
    """
    Signal receiver to update the user's subscription status upon successful payment.
    """
    if instance.is_sucessful:
        instance.process_payment()
        logger.info(f"Processed payment for user: {instance.user.username}")


@receiver(post_delete, sender=PremiumSubscription)
def inform_subscription(sender, instance, **kwargs):
    user = instance.user
    try:
        if not user.is_premium:  
            send_extend_premium_account(user)
            logger.info(f"Sent premium extension email to {user.email}")
    except Exception as error:
        logger.error(f"Email failed for user {user.email}: {error}", exc_info=True)
        
    
#========================================================================================================