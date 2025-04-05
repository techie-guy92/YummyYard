from rest_framework import serializers
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
    # user = serializers.HiddenField(default=None)
    
    class Meta:
        model = Wishlist
        fields = ["id", "user", "product", "product_price", "product_name"]
        extra_kwargs = {"user": {"read_only": True}}
        
        
#====================================== ShoppingCart Serializer ============================================

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["product", "quantity", "grand_total"]
        
        
class ShoppingCartSerializer(serializers.Serializer):
    cart_items = CartItemSerializer(many=True, write_only=True)
    total_price = serializers.IntegerField(read_only=True)
    
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
                    CartItem.objects.create(cart=cart, **item_data )
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
                    if coupon.usage_count >= coupon.max_usage:
                        coupon.is_active = False
                        coupon.save(update_fields=["is_active"])
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

class TransactionSerializer(serializers.ModelSerializer):
    pass
        
        
#====================================== UserView Serializer ================================================

class UserViewSerializer(serializers.ModelSerializer):
    pass
        
        
#====================================== Rating Serializer ==================================================

class RatingSerializer(serializers.ModelSerializer):
    pass
        
        
#===========================================================================================================