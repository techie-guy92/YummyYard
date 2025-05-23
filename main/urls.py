from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from .views import (get_product_price, get_cart_price, WishlistModelViewSet, ShoppingCartAPIView, DeliveryScheduleAPIView,
                    DeliveryScheduleChangeAPIView, CategoryModelViewSet, ProductModelViewSet, OrderAPIView, OrderCancellationAPIView, 
                    RatingModelViewSet, TransactionModelViewSet, DeliveryAPIView, UserViewModelViewSet)


router =  DefaultRouter()
router.register(r"categories", CategoryModelViewSet, basename="categories")
router.register(r"products", ProductModelViewSet, basename="products")
router.register(r"wishlist", WishlistModelViewSet, basename="wishlist")
router.register(r"add_products", ShoppingCartAPIView, basename="add_products")
router.register(r"payment", TransactionModelViewSet, basename="payment")
router.register(r"last_seen", UserViewModelViewSet, basename="last_seen")
router.register(r"ratings", RatingModelViewSet, basename="ratings")

    
urlpatterns = [
    path("get_product_price/<int:product_id>/", get_product_price, name="get_product_price"),
    path("get_cart_price/<int:cart_id>/", get_cart_price, name="get_cart_price"),
    path("add_schedule/", DeliveryScheduleAPIView.as_view(), name="add_schedule"),
    path("change_schedule/<int:delivery_id>/", DeliveryScheduleChangeAPIView.as_view(), name="change_schedule"),
    path("complete_order/", OrderAPIView.as_view(), name="complete_order"),
    path("cancel_order/<int:order_id>/", OrderCancellationAPIView.as_view(), name="cancel_order"),
    path("complete_delivery/", DeliveryAPIView.as_view(), name="complete_delivery"),
    path("<int:product_id>/last_seen/", UserViewModelViewSet.as_view({"get": "list", "post": "create"}), name="last_seen_by_product_id"),
    path("<int:product_id>/ratings/", RatingModelViewSet.as_view({"get": "list", "post": "create"}), name="ratings_by_product_id"),

] 


urlpatterns += router.urls