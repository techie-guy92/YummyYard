import os
os.environ["DJANGO_SETTINGS_MODULES"]= "config.settings"
import django
django.setup()

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from jwt import decode
from django.urls import resolve, reverse
from .models import *
from .serializers import *
from .views import *
from .urls import *
from users_constant import *
from products_constant import *
from utilities import create_test_users, create_test_categories, create_test_products


#====================================== Gategory Test ===================================================

class GategoryTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("categories-list")

    def test_category_model(self):
        pass
    
    def test_category_serializer(self):
        pass
    
    def test_category_view(self):
        pass
    
    def test_category_url(self):
        pass
    

#====================================== Product Test ====================================================

class ProductTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("products-list")

    def test_product_model(self):
        pass
    
    def test_product_serializer(self):
        pass
    
    def test_product_view(self):
        pass
    
    def test_product_url(self):
        pass


#====================================== Wishlist Test ===================================================

class WishlistTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("wishlist-list")

    def test_wishlist_model(self):
        pass
    
    def test_wishlist_serializer(self):
        pass
    
    def test_wishlist_view(self):
        pass
    
    def test_wishlist_url(self):
        pass
    
    
#====================================== ShoppingCart Test ===============================================

class ShoppingCartTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("add_products-list")

    def test_shopping_cart_model(self):
        pass
    
    def test_shopping_cart_serializer(self):
        pass
    
    def test_shopping_cart_view(self):
        pass
    
    def test_shopping_cart_url(self):
        pass
    
    
#====================================== Delivery Schedule Test ==========================================

class DeliveryScheduleTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("add_schedule")

    def test_delivery_schedule_model(self):
        pass
    
    def test_delivery_schedule_serializer(self):
        pass
    
    def test_delivery_schedule_view(self):
        pass
    
    def test_delivery_schedule_url(self):
        pass
    
    
#====================================== Delivery Schedule Change Test ===================================

class DeliveryScheduleChangeTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.delivery_id = 44
        self.url = reverse("change_schedule", kwargs={"delivery_id": self.delivery_id})

    def test_delivery_schedule_change_serializer(self):
        pass
    
    def test_delivery_schedule_change_view(self):
        pass
    
    def test_delivery_schedule_change_url(self):
        pass
    
    
#====================================== Order Test ======================================================

class OrderTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("complete_order")

    def test_order_model(self):
        pass
    
    def test_order_serializer(self):
        pass
    
    def test_order_view(self):
        pass
    
    def test_order_url(self):
        pass
    
    
#====================================== Order Cancellation Test =========================================

class OrderCancellationTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.order_id = 55
        self.url = reverse("cancel_order", kwargs={"order_id": self.order_id})
    
    def test_order_cancellation_serializer(self):
        pass
    
    def test_order_cancellation_view(self):
        pass
    
    def test_order_cancellation_url(self):
        pass
    
    
#====================================== Delivery Test ===================================================

class DeliveryTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("complete_delivery")

    def test_delivery_model(self):
        pass
    
    def test_delivery_serializer(self):
        pass
    
    def test_delivery_view(self):
        pass
    
    def test_delivery_url(self):
        pass
    
    
#====================================== UserView Test ===================================================

class UserViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.product_id = 1
        self.url = reverse("last_seen-list")
        self.url_2 = reverse("last_seen_by_product_id", kwargs={"product_id": self.product_id})

    def test_user_view_model(self):
        pass
    
    def test_user_view_serializer(self):
        pass
    
    def test_user_view_view(self):
        pass
    
    def test_user_view_url(self):
        pass
    
    
#====================================== Rating Test =====================================================

class RatingTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.product_id = 1
        self.url = reverse("ratings-list")
        self.url_2 = reverse("ratings_by_product_id", kwargs={"product_id": self.product_id})

    def test_rating_model(self):
        pass
    
    def test_rating_serializer(self):
        pass
    
    def test_rating_view(self):
        pass
    
    def test_rating_url(self):
        pass
    
    
#========================================================================================================
