from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from .views import get_product_price, get_cart_price


router =  DefaultRouter()
# router.register(f"")


urlpatterns = [
    path("get_product_price/<int:product_id>/", get_product_price, name="get_product_price"),
    path("get_cart_price/<int:cart_id>/", get_cart_price, name="get_cart_price"),
] 

# urlpatterns += router.urls