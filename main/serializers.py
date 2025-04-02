from rest_framework import serializers
from .models import *
from users.models import *


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
    pass
        
        
#====================================== Order Serializer ===================================================

class OrderSerializer(serializers.ModelSerializer):
    pass
        
        
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

# class DeliveryScheduleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DeliverySchedule
#         fields = ["id", "shopping_cart", "user", "date", "time", "delivery_method", "delivery_cost"]

#     def validate(self, data):
#         if data.get("shopping_cart") and data.get("user"):
#             cart_user = data["shopping_cart"].online_customer
#             if cart_user and cart_user != data["user"]:
#                 raise serializers.ValidationError(
#                     "User and ShoppingCart's online_customer must match."
#                 )
#         return data

#     def create(self, validated_data):
#         instance = super().create(validated_data)
#         instance.reserve_delivery_slot()
#         return instance