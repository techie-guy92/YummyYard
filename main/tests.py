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
from constants import primary_user_1, primary_user_2, primary_user_3, primary_user_4, primary_user_5, invalid_user_1
from utilities import create_test_users


#====================================== Gategory Test ===================================================

class GategoryTest(APITestCase):
    pass


#====================================== Product Test ====================================================

class ProductTest(APITestCase):
    pass


#====================================== Wishlist Test ===================================================

class WishlistTest(APITestCase):
    pass


#====================================== ShoppingCart Test ===============================================

class ShoppingCartTest(APITestCase):
    pass


#====================================== Delivery Schedule Test ==========================================

class DeliveryScheduleTest(APITestCase):
    pass


#====================================== Delivery Schedule Change Test ===================================

class DeliveryScheduleChangeTest(APITestCase):
    pass


#====================================== Order Test ======================================================


class OrderTest(APITestCase):
    pass


#====================================== Order Cancellation Test =========================================


class OrderCancellationTest(APITestCase):
    pass


#====================================== Delivery Test ===================================================


class DeliveryTest(APITestCase):
    pass


#====================================== UserView Test ===================================================

class UserViewTest(APITestCase):
    pass


#====================================== Rating Test =====================================================

class RatingTest(APITestCase):
    pass


#========================================================================================================
