from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from .views import (get_product_price, get_cart_price, WishlistModelViewSet, ShoppingCartAPIView, DeliveryScheduleAPIView,
                    CategoryModelViewSet, ProductModelViewSet, OrderAPIView, )


router =  DefaultRouter()
router.register(r"categories", CategoryModelViewSet, basename="categories")
router.register(r"products", ProductModelViewSet, basename="products")
router.register(r"wishlist", WishlistModelViewSet, basename="wishlist")
router.register(r"add_products", ShoppingCartAPIView, basename="add_products")

    
urlpatterns = [
    path("get_product_price/<int:product_id>/", get_product_price, name="get_product_price"),
    path("get_cart_price/<int:cart_id>/", get_cart_price, name="get_cart_price"),
    path("add_schedule/", DeliveryScheduleAPIView.as_view(), name="add_schedule"),
    path("complete_order/", OrderAPIView.as_view(), name="complete_order")
] 


urlpatterns += router.urls