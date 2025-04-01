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
    pass
        
        
class ShoppingCartSerializer(serializers.Serializer):
    pass
        
        
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