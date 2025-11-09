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
        if instance.is_active and instance.is_expired():
            logger.info(f"Coupon {instance.code} has expired.")
            instance.is_active = False
            instance.save(update_fields=["is_active"])
            logger.info(f"Coupon {instance.code} deactivated due to expiration.")
        if instance.is_active and instance.usage_count > instance.max_usage:
            logger.info(f"Coupon {instance.code} has reached its maximum usage.")
            instance.is_active = False
            instance.save(update_fields=["is_active"])
            logger.info(f"Coupon {instance.code} deactivated due to maximum usage.")
        if instance.is_active:
            logger.debug(f"Coupon {instance.code} is still valid.")
    except Exception as error:
        logger.error(f"Error in check_coupon_expiration signal: {error}", exc_info=True)


#==================================== UpdateWarehouse Signal ===========================================

@receiver(post_save, sender=Warehouse)
def handle_update_stock(sender, instance, created, **kwargs):
    product = instance.product
    total_stock = Warehouse.total_stock(product=product)
    is_available = total_stock > 0
    # Update directly without triggering save()
    Warehouse.objects.filter(product=product).update(is_available=is_available)


#==================================== UpdateOrder Signal ===============================================

@receiver(post_save, sender=CartItem)
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
        shopping_cart.clear_cart()
        logger.debug(f"Order ID {instance.id} triggered place_order and clear_cart for ShoppingCart ID {shopping_cart.id}")  


@receiver(post_save, sender=Order)
def set_order_status(sender, instance, created, **kwargs):
    try:
        if created and instance.status == "on_hold":
            instance.status = "waiting"
            instance.save(update_fields=["status"])
            logger.info(f"Order ID {instance.id} status changed to 'waiting' after placing.")
        # Only restore stock if status just changed to canceled
        previous = Order.objects.get(pk=instance.pk)
        if previous.status != "canceled" and instance.status == "canceled":
            instance.restore_stock()
            logger.info(f"Order ID {instance.id} was canceled and products returned to stock.")
    except Exception as error:
        logger.error(f"Error in set_order_status signal for Order ID {instance.id}: {error}", exc_info=True)


@receiver(post_save, sender=Delivery)
def send_tracking_id(sender, instance, **kwargs):
    tracking_id = instance.tracking_id
    customer = instance.order.online_customer
    delivery_schedule = instance.order.delivery_schedule
    if not customer:
        logger.error(f"Delivery {instance.id} has no assigned customer. Email cannot be sent.")
        return
    if instance.order.status == "successful":
        delivery_date = delivery_schedule.date.strftime("%Y-%m-%d") if delivery_schedule else "Not Scheduled"
        subject = "Tracking id"
        html_content = f"""Hello dear {customer.first_name} {customer.last_name},<br><br>
        Your payment was successfully completed, and your order will be delivered on <b>{delivery_date} at {delivery_schedule.time}</b>.
        <br>Your tracking ID is: <b>{tracking_id}</b>. Please provide this code to the postman."""
        try:
            email_sender(subject, "", html_content, [customer.email])
        except Exception as error:
            logger.error(f"Failed to send tracking email to {customer.email}: {error}")


@receiver(post_save, sender=Delivery)
def handle_delivery_status_shipped(sender, instance, **kwargs):
    try:
        crr_datetime = localtime(now())
        logger.debug(f"Signal triggered for Delivery ID {instance.id} with status 'shipped' at {crr_datetime}.")
        if instance.status == "shipped" and not instance.shipped_at:
            def update_status():
                instance.shipped_at = crr_datetime
                instance.order.status = "shipped"
                instance.save(update_fields=["shipped_at"])
                instance.order.save(update_fields=["status"])
                logger.info(f"Delivery ID {instance.id} shipped at {instance.shipped_at}. Order ID {instance.order.id} marked as 'shipped'.")
            # Defer critical updates until transaction is committed. It is used when deferring non-critical operations until the transaction is finalized
            transaction.on_commit(update_status)
        else:
            logger.debug(f"Delivery ID {instance.id} is not marked as 'shipped'. No updates performed.")
    except Exception as error:
        logger.error(f"Error in handle_delivery_status_shipped signal for Delivery ID {instance.id}: {error}", exc_info=True)


#========================================================================================================