import os
os.environ["DJANGO_SETTINGS_MODULES"]= "config.settings"
import django
django.setup()

from rest_framework.test import APITestCase, APIClient, APIRequestFactory
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
        view = resolve("/products/categories/")
        self.assertEqual(view.func.cls, CategoryModelViewSet)
    

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
        view = resolve("/products/products/")
        self.assertEqual(view.func.cls, ProductModelViewSet)


#====================================== Wishlist Test ===================================================

class WishlistTest(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.url = reverse("wishlist-list")
        self.request = self.factory.post(self.url)
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.c1, self.c2, self.c3, self.c4, self.c5, self.c6, self.c7 = create_test_categories()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()
        self.wishlist_1 = Wishlist.objects.create(user=self.user_1, product=self.p1)
        
    def test_wishlist_model(self):
        self.assertEqual(str(self.wishlist_1), f"Wishlist of {self.user_1.username}")
    
    def test_wishlist_serializer(self):
        if self.wishlist_1:
            self.wishlist_1.delete()
        self.request.user = self.user_1 
        serializer = WishlistSerializer(data={"product": self.p1.id}, context={"request": self.request})  
        self.assertTrue(serializer.is_valid(raise_exception=True))
        serializer.save()
        ser_data = serializer.data
        self.assertEqual(ser_data["product"], self.p1.id)  

    def test_wishlist_view(self):
        self.client.force_authenticate(user=self.user_1) 
        if self.wishlist_1:
            self.wishlist_1.delete()
        response = self.client.post(self.url, {"product": self.p1.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["product"], self.p1.id)
        
    def test_wishlist_url(self):
        view = resolve("/products/wishlist/")
        self.assertEqual(view.func.cls, WishlistModelViewSet)
    
    
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
        view = resolve("/products/add_products/")
        self.assertEqual(view.func.cls, ShoppingCartAPIView)
    
    
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
        view = resolve("/products/add_schedule/")
        self.assertEqual(view.func.cls, DeliveryScheduleAPIView)
    
    
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
        view = resolve("/products/complete_order/")
        self.assertEqual(view.func.cls, OrderAPIView)
    
    
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
        view = resolve("/products/complete_delivery/")
        self.assertEqual(view.func.cls, DeliveryAPIView)
    
    
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
        view = resolve("/products/last_seen/")
        self.assertEqual(view.func.cls, UserViewModelViewSet)
    
    
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
        view = resolve("/products/ratings/")
        self.assertEqual(view.func.cls, RatingModelViewSet)
    
    
#========================================================================================================
