from rest_framework import serializers
from .models import *
from users.models import *


#====================================== Wishlist Serializer ================================================
#====================================== ShoppingCart Serializer ============================================
#====================================== Delivery Schedule Serializer =======================================
#====================================== Order Serializer ===================================================
#====================================== Transaction Serializer =============================================
#====================================== UserView Serializer ================================================
#====================================== Rating Serializer ==================================================
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