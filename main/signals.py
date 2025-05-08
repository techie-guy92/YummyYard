from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, post_delete
from logging import getLogger
from django.db import transaction
from .models import *
from utilities import *

#==================================== UpdateCoupon Signal ===============================================

logger = getLogger(__name__)


@receiver(post_save, sender=Coupon)
def check_coupon_expiration(sender, instance, **kwargs):
    try:
        logger.debug(f"Signal triggered for coupon: {instance.code}. Current time: {localtime(now())}, Valid To: {instance.valid_to}")
        instance.refresh_from_db()
        if instance.is_expired() and instance.is_active:
            logger.info(f"Coupon {instance.code} has expired.")
            instance.is_active = False
            instance.save(update_fields=["is_active"])
            logger.info(f"Coupon {instance.code} deactivated due to expiration.")
        if instance.usage_count > instance.max_usage and instance.is_active:
            logger.info(f"Coupon {instance.code} has reached its maximum usage.")
            instance.is_active = False
            instance.save(update_fields=["is_active"])
            logger.info(f"Coupon {instance.code} deactivated due to maximum usage.")
        if instance.is_active:
            logger.debug(f"Coupon {instance.code} is still valid.")
    except Exception as error:
        logger.error(f"Error in check_coupon_expiration signal: {error}", exc_info=True)


#==================================== UpdateOrder Signal ===============================================

@receiver(post_save, sender=Warehouse)
def handle_update_stock(sender, instance, created, **kwargs):
    product = instance.product
    total_stock = Warehouse.total_stock(product=product)
    is_available = total_stock > 0
    # Update directly without triggering save()
    Warehouse.objects.filter(product=product).update(is_available=is_available)


@receiver(post_save, sender=CartItem)
@receiver(post_delete, sender=CartItem)
def update_cart_total_price(sender, instance, created, **kwargs):
    cart = instance.cart
    if cart:
        cart.total_price = cart.calculate_total_price()
        cart.save(update_fields=["total_price"])


@receiver(post_save, sender=Order)
def handle_place_order(sender, instance, created, **kwargs):
    if created:  
        shopping_cart = instance.shopping_cart 
        shopping_cart.place_order()
        logger.debug(f"Order ID {instance.id} triggered place_order for ShoppingCart ID {shopping_cart.id}")  


@receiver(post_save, sender=Order)
def set_order_status_to_waiting(sender, instance, created, **kwargs):
    try:
        if created and instance.status == "on_hold":
            instance.status = "waiting"
            instance.save(update_fields=["status"])
            logger.info(f"Order ID {instance.id} status changed to 'waiting' after placing.")
    except Exception as error:
        logger.error(f"Error in set_order_status_to_waiting signal for Order ID {instance.id}: {error}", exc_info=True)


@receiver(post_save, sender=Delivery)
def handle_delivery_status_shipped(sender, instance, **kwargs):
    try:
        logger.debug(f"Signal triggered for Delivery ID {instance.id} with status 'shipped' at {localtime(now())}.")

        if instance.status == "shipped":
            def update_status():
                instance.shipped_at = localtime(now())
                instance.order.status = "shipped"
                instance.save(update_fields=["shipped_at"])
                instance.order.save(update_fields=["status"])
                logger.info(
                    f"Delivery ID {instance.id} shipped at {instance.shipped_at}. Order ID {instance.order.id} marked as 'shipped'."
                )

            # Defer critical updates until transaction is committed. It is used when deferring non-critical operations until the transaction is finalized
            transaction.on_commit(update_status)
        else:
            logger.debug(f"Delivery ID {instance.id} is not marked as 'shipped'. No updates performed.")
    except Exception as error:
        logger.error(f"Error in handle_delivery_status_shipped signal for Delivery ID {instance.id}: {error}", exc_info=True)


# @receiver(post_save, sender=Delivery)
# def handle_delivery_status_delivered(sender, instance, created, **kwargs):
#     try:
#         logger.debug(f"Signal triggered for Delivery ID {instance.id} with status '{instance.status}'.")
#         # It is used when we need to lock rows for concurrency control
#         db_delivery = Delivery.objects.select_for_update().get(pk=instance.pk)
#         if instance.tracking_id == db_delivery.tracking_id:
#             logger.info(f"Tracking ID match confirmed for Delivery ID {instance.id}. Proceeding with status update.")
#             instance.delivered_at = localtime(now())
#             instance.status = "completed"
#             instance.order.status = "completed"
#             with transaction.atomic():
#                 instance.save(update_fields=["status", "delivered_at"])
#                 instance.order.save(update_fields=["status"])
#             logger.info(
#                 f"Delivery ID {instance.id} marked as 'completed' at {instance.delivered_at}. "
#                 f"Order ID {instance.order.id} status updated to 'completed'."
#             )
#         else:
#             logger.warning(
#                 f"[Tracking Mismatch] Delivery ID {instance.id} - DB Tracking ID: {db_delivery.tracking_id}, "
#                 f"Instance Tracking ID: {instance.tracking_id}."
#             )
#             return
#     except Delivery.DoesNotExist:
#         logger.error(f"Delivery ID {instance.id} not found in database during processing.")
#     except Exception as error:
#         logger.error(f"Critical error in handle_delivery_status_delivered signal for Delivery ID {instance.id}: {error}", exc_info=True)
        
      
#========================================================================================================