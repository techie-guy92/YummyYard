from rest_framework import serializers
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from .models import *
from users.models import *


#====================================== Gategory Serializer ================================================

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
   
    class Meta:
        model = Category
        fields = ["id", "name", "parent", "slug", "description", "image", "children"]

    def get_children(self, obj):
        return CategorySerializer(obj.Category_parent.all(), many=True).data
        
        
#====================================== Product Serializer =================================================

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "category", "slug", "price", "description", "image"]
        
        
#====================================== Wishlist Serializer ================================================

class WishlistSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")
    product_price = serializers.ReadOnlyField(source="product.price")
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = Wishlist
        fields = ["id", "user", "product", "product_name", "product_price"]
        # extra_kwargs = {"user": {"read_only": True}}
        
        
#====================================== ShoppingCart Serializer ============================================

class CartItemSerializer(serializers.ModelSerializer): 
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True)  
    product_name = serializers.SerializerMethodField()
    grand_total = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = ["product", "product_name", "quantity", "grand_total"]
        
    def get_product_name(self, obj):
        return obj.product.name
        
        
class ShoppingCartSerializer(serializers.Serializer):
    cart_items = CartItemSerializer(many=True, write_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = ShoppingCart
        fields = ["cart_items", "total_price"] 
        
    def create(self, validated_data):
        cart_items_data = validated_data.pop("cart_items")
        request = self.context.get("request")
        validated_data["online_customer"] = request.user
        try:
            with transaction.atomic():
                cart = ShoppingCart.objects.create(**validated_data)
                for item_data in cart_items_data:
                    CartItem.objects.create(cart=cart, **item_data)
                cart.total_price = cart.calculate_total_price()
                cart.save(update_fields=["total_price"])
                return cart
        except ValidationError as error:
            raise serializers.ValidationError({"error": str(error)})
        except Exception as error:
            raise serializers.ValidationError({"error": "An unexpected error occurred."})
        

#====================================== Delivery Schedule Serializer =======================================

class DeliveryScheduleSerializer(serializers.ModelSerializer):
    delivery_cost = serializers.ReadOnlyField()
    day = serializers.ReadOnlyField()
    
    class Meta:
        model = DeliverySchedule
        fields = ["delivery_method", "date", "day", "time", "delivery_cost"]
        extra_kwargs = {"user": {"read_only": True}, "shopping_cart": {"read_only": True}}

    # def create(self, validated_data):
    #     request = self.context.get("request")
    #     validated_data["user"] = request.user
    #     validated_data["shopping_cart"] = ShoppingCart.objects.filter(online_customer=request.user).last()
    #     if not validated_data["shopping_cart"]:
    #         raise serializers.ValidationError("No active shopping cart found.")
    #     return super().create(validated_data)
    
    def validate(self, data):
        if not ShoppingCart.objects.filter(online_customer=self.context["request"].user).exists():
            raise serializers.ValidationError("No active shopping cart found. Please add products to your cart before scheduling delivery.")
        return data

         
#====================================== Order Serializer ===================================================

class OrderSerializer(serializers.ModelSerializer):
    discount = serializers.CharField(max_length=10, write_only=True, required=False)

    class Meta:
        model = Order
        fields = ["discount"]

    def create(self, validated_data):
        discount_code = validated_data.pop("discount", None)
        request = self.context.get("request")
        customer = request.user

        validated_data["online_customer"] = customer
        validated_data["order_type"] = "online"
        validated_data["payment_method"] = "online"

        cart, delivery = self.validate_order_components(customer)
        validated_data["shopping_cart"] = cart
        validated_data["delivery_schedule"] = delivery
        validated_data["total_amount"] = validated_data["shopping_cart"].total_price + validated_data["delivery_schedule"].delivery_cost

        with transaction.atomic():
            if discount_code:
                try:
                    coupon = Coupon.objects.get(code=discount_code, is_active=True)
                    if not coupon.is_valid():
                        raise serializers.ValidationError("The discount code is no longer valid or has expired.")
                    discount_amount = validated_data["total_amount"] * (coupon.discount_percentage / 100)
                    validated_data["discount_applied"] = discount_amount
                    validated_data["amount_payable"] = validated_data["total_amount"] - discount_amount
                    validated_data["coupon"] = coupon 
                    coupon.usage_count = models.F("usage_count") + 1
                    coupon.save(update_fields=["usage_count"])
                    coupon.refresh_from_db()
                except Coupon.DoesNotExist:
                    raise serializers.ValidationError("Invalid discount code.")

            order = Order.objects.create(**validated_data)
            return order

    def validate_order_components(self, customer):
        cart = ShoppingCart.objects.filter(online_customer=customer).last()
        delivery = DeliverySchedule.objects.filter(user=customer, shopping_cart=cart).first()
        order = Order.objects.filter(online_customer=customer, shopping_cart=cart).first()
        if not cart:
            raise serializers.ValidationError("No active shopping cart found.")
        if not delivery:
            raise serializers.ValidationError("No delivery schedule found.")
        if order:
            raise serializers.ValidationError("An order already exists for this cart.")
        return cart, delivery
            
        
#====================================== Transaction Serializer =============================================

# Note: This class is a placeholder for future integration with a payment gateway. 
# It is currently defined as a sample and does not include the full implementation.

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["user", "amount", "payment_id", "is_successful"]
        
        
#====================================== UserView Serializer ================================================

class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserView
        fields = ["user", "product", "last_seen", "view_count"]
        read_only_fields = ["user", "last_seen", "view_count"]

    def create(self, validated_data):
        user = self.context.get("request").user
        product = validated_data.get("product")
        product_id = self.context.get("view").kwargs.get("product_id") or (product.id if product else None)
        if not product_id:
            raise serializers.ValidationError("Product ID is required. Please provide it in the URL or JSON payload.")
        product = get_object_or_404(Product, id=product_id)
        try:
            user_view, created = UserView.objects.get_or_create(user=user, product=product)
            if not created:
                user_view.last_seen = timezone.now()
                user_view.view_count += 1
                user_view.save()
            return user_view
        except Exception as error:
            raise serializers.ValidationError(f"Failed to create or update UserView: {str(error)}")


#====================================== Rating Serializer ==================================================

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ["rating", "review"]
        extra_kwargs = {"user": {"read_only": True}, "product": {"read_only": True}}

    def validate(self, data):
        request = self.context.get("request")
        product = self.context.get("product") 
        customer = request.user
        if not product:
            product_id = self.context.get("view").kwargs.get("product_id") or self.initial_data.get("product")
            product = get_object_or_404(Product, id=product_id)
        has_completed_order = Order.objects.filter(online_customer=customer, status="completed", shopping_cart__products=product).exists()
        if not has_completed_order:
            raise serializers.ValidationError("You can only rate this product if you have completed an order for it.")
        return data

        
#===========================================================================================================