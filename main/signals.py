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


def cancel_cart(order):
    with transaction.atomic():
        order.restore_stock()
        order.shopping_cart.status = "abandoned"
        order.shopping_cart.save(update_fields=["status"])
        CartItem.objects.filter(cart=order.shopping_cart, status__in=["processed"]).update(status="abandoned")
        logger.info(f"Order {order.id} canceled — stock restored and cart abandoned")


@receiver(post_save, sender=Order)
def handle_order_workflow(sender, instance, created, **kwargs):
    try:
        if created:
            with transaction.atomic():
                if not instance.order_number:
                    instance.order_number = instance.generate_order_number()
                    instance.save(update_fields=["order_number"])
                shopping_cart = instance.shopping_cart
                shopping_cart.place_order()
                shopping_cart.clear_cart()
                if instance.status == "on_hold":
                    Order.objects.filter(pk=instance.pk).update(status="waiting")
                logger.info(f"Order {instance.id} processed — Cart {shopping_cart.id}")

        if not created:
            if instance.status == "canceled" and instance.shopping_cart.status != "abandoned":
                transaction_obj = Transaction.objects.filter(order=instance.pk).first()
                if not transaction_obj or not transaction_obj.is_paid:
                    cancel_cart(instance)
                else:
                    cancel_cart(instance)
                    with transaction.atomic():
                        Order.objects.filter(pk=instance.pk).update(status="refunded")
                        refund, created = Refund.objects.get_or_create(order=instance, defaults={
                            "wallet": instance.wallet.balance,
                            "amount": instance.amount_payable,
                            "method": "wallet",
                            "status": "requested",
                        })
                        if created:
                            logger.info(f"Refund created for Order {instance.id} — Amount: {refund.amount}")
                        else:
                            logger.debug(f"Refund already exists for Order {instance.id}")
            elif instance.status == "canceled" and instance.shopping_cart.status == "abandoned":
                logger.debug(f"Order {instance.id} already processed as canceled")
    except Exception as error:
        logger.error(f"Order signal error {instance.id}: {error}", exc_info=True)


def create_delivery_for_order(order):
    delivery, created = Delivery.objects.get_or_create(
        order=order,
        defaults={
            "tracking_id": f"TRK-{order.id}-{uuid4().hex[:5].upper()}",
            "status": "pending"
        }
    )
    if created:
        logger.info(f"Auto-created delivery {delivery.id} for paid order {order.id}")


@receiver(post_save, sender=Transaction)
def handle_successful_payment(sender, instance, created, **kwargs):
    if created:
        if instance.is_paid and instance.order.status == "waiting" and instance.order.order_type == "online":
            with transaction.atomic():
                Order.objects.filter(pk=instance.order.pk).update(status="successful")
                create_delivery_for_order(instance.order)
        elif instance.is_paid and instance.order.status == "waiting" and instance.order.order_type == "in_person":
            with transaction.atomic():
                Order.objects.filter(pk=instance.order.pk).update(status="completed")
            logger.info(f"Order {instance.order.id} which is in-person order is successfully paid and completed.")
        

@receiver(post_save, sender=Delivery)
def send_tracking_id(sender, instance, created, **kwargs):
    if created:
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


# @receiver(post_save, sender=Refund)
# def handle_refund_completion(sender, instance, **kwargs):
#     if instance.status == "completed" and instance.method == "wallet":
#         wallet, created = Wallet.objects.get_or_create(
#             wallet=instance.wallet,
#             defaults={'balance': 0}
#         )
#         wallet.balance += instance.amount
#         wallet.save()
#         logger.info(f"Credited {instance.amount} to wallet for refund {instance.id}")
            

#========================================================================================================