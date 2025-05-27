import os
os.environ["DJANGO_SETTINGS_MODULES"] = "config.settings"
import django
django.setup()

from rest_framework.test import APITestCase, APIClient, APIRequestFactory
from rest_framework import status
from django.urls import resolve, reverse
from django.utils.timezone import localtime, now
from .models import *
from .serializers import *
from .views import *
from .urls import *
from users_constant import *
from products_constant import *
from utilities import create_test_users, create_test_categories, create_test_products


#====================================== Gategory Test ===================================================

class CategoryTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("categories-list")
        self.c1, self.c2, self.c3, self.c4, self.c5, self.c6, self.c7 = create_test_categories()
        
    def test_category_model(self):
        self.assertEqual(str(self.c1), self.c1.name) 

    def test_category_serializer(self):
        serializer = CategorySerializer(instance=self.c1)
        ser_data = serializer.data
        self.assertEqual(ser_data["name"], self.c1.name)
    
    def test_category_view(self):
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK) 
        self.assertIn("results", response.data) 
        # Ensures that result is not empty and it contains at least one item
        self.assertGreater(len(response.data.get("results", [])), 0) 
        self.assertEqual(response.data["results"][0]["name"], self.c1.name) 

    def test_category_url(self):
        view = resolve("/products/categories/")
        self.assertEqual(view.func.cls, CategoryModelViewSet)
        self.assertIsInstance(view.func.cls, type)


#====================================== Product Test ====================================================

class ProductTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("products-list")
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()

    def test_product_model(self):
        self.assertEqual(str(self.p1), self.p1.name)
    
    def test_product_serializer(self):
        serializer = ProductSerializer(instance=self.p1)
        ser_data = serializer.data
        self.assertEqual(ser_data["name"], self.p1.name)
        self.assertEqual(ser_data["price"], self.p1.price)
    
    def test_product_view(self):
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreater(len(response.data.get("results", [])), 0) 
        self.assertEqual(response.data["results"][0]["name"], Product.objects.order_by("-price").first().name)  
    
    def test_product_url(self):
        view = resolve("/products/products/")
        self.assertEqual(view.func.cls, ProductModelViewSet)
        self.assertIsInstance(view.func.cls, type)


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
        self.assertIsInstance(view.func.cls, type)
        
    
#====================================== ShoppingCart Test ===============================================

class ShoppingCartTest(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.url = reverse("add_products-list")
        self.request = self.factory.post(self.url)
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()
        self.increment_stock_1 = Warehouse.objects.create(product=self.p1, stock=50)
        self.increment_stock_2 = Warehouse.objects.create(product=self.p2, stock=50)
        self.increment_stock_3 = Warehouse.objects.create(product=self.p3, stock=50)
        self.cart_1 = ShoppingCart.objects.create(online_customer=self.user_1)
        self.cart_item_1 = CartItem.objects.create(cart=self.cart_1, product=self.p1, quantity=2)
        self.cart_item_2 = CartItem.objects.create(cart=self.cart_1, product=self.p2, quantity=3)
        self.cart_1.save()
        self.cart_2 = {"online_customer": self.user_1.id, "cart_items": [{"product": self.p1.id, "quantity": 2}, {"product": self.p2.id, "quantity": 3}]}
        self.invalid_cart = {"online_customer": None, "cart_items": [{"product": self.p1.id, "quantity": -1}],}
        self.empty_cart = {"online_customer": self.user_1.id, "cart_items": []} 

    def test_cart_item_linking(self):
        self.assertEqual(self.cart_1.products.count(), 2)  
        self.assertGreater(len(self.cart_1.products.all()), 1)  
        self.assertTrue(self.cart_1.products.filter(id=self.p1.id).exists())  
        self.assertTrue(self.cart_1.products.filter(id=self.p2.id).exists())  

    def test_shopping_cart_model(self):
        expected_total = (self.cart_item_1.quantity * self.p1.price) + (self.cart_item_2.quantity * self.p2.price)
        self.assertEqual(self.cart_1.total_price, expected_total)
        self.assertEqual(str(self.cart_1), f"{self.cart_1.id} - {self.user_1.username}")
      
    def test_shopping_cart_serializer(self):
        self.request.user = self.user_1
        serializer = ShoppingCartSerializer(data=self.cart_2, context={"request": self.request})
        self.assertTrue(serializer.is_valid(raise_exception=True))
        serializer.save()
        ser_data = serializer.data
        self.assertEqual(ser_data["total_price"], 115400)   
    
    def test_shopping_cart_invalid_data(self):
        serializer = ShoppingCartSerializer(data=self.invalid_cart, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        
    def test_shopping_cart_view(self):
        self.client.force_authenticate(self.user_1)
        response = self.client.post(self.url, self.cart_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "کالاهای شما اضافه شد.")
        self.assertEqual(response.data["cart_items_count"], 2)
        self.assertIn("cart_items", response.data)
        self.assertEqual([item["product_name"] for item in response.data["cart_items"]], [self.p1.name, self.p2.name])  
    
    def test_shopping_cart_empty(self): 
        self.client.force_authenticate(self.user_1)
        response = self.client.post(self.url, self.empty_cart, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "سبد خرید نمی‌تواند خالی باشد.") 

    def test_shopping_cart_url(self):
        view = resolve("/products/add_products/")
        self.assertEqual(view.func.cls, ShoppingCartAPIView)
        self.assertIsInstance(view.func.cls, type)
        

#====================================== Delivery Schedule Test ==========================================

class DeliveryScheduleTest(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.url = reverse("add_schedule")
        self.request = self.factory.post(self.url)
        self.crr_datetime = localtime(now())
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()
        self.increment_stock_1 = Warehouse.objects.create(product=self.p1, stock=50)
        self.increment_stock_2 = Warehouse.objects.create(product=self.p2, stock=50)
        self.increment_stock_3 = Warehouse.objects.create(product=self.p3, stock=50)
        self.cart = ShoppingCart.objects.create(online_customer=self.user_1)
        self.cart_item_1 = CartItem.objects.create(cart=self.cart, product=self.p1, quantity=2)
        self.cart_item_2 = CartItem.objects.create(cart=self.cart, product=self.p2, quantity=3)
        self.cart.save()
        self.delivery_schadule_1 = {"user": self.user_1, "shopping_cart": self.cart, "delivery_method": "normal", "date": self.crr_datetime.date(), "time": "20_22"}
        self.delivery_schadule_2 = {"user": self.user_1, "shopping_cart": self.cart, "delivery_method": "normal", "date": self.crr_datetime.date(), "time": "8_10"}
        self.valid_payload_1 = {"delivery_method": self.delivery_schadule_1["delivery_method"], "date": str(self.delivery_schadule_1["date"]), "time": self.delivery_schadule_1["time"]}
        self.valid_payload_2 = {"delivery_method": self.delivery_schadule_2["delivery_method"], "date": str(self.delivery_schadule_2["date"]), "time": self.delivery_schadule_2["time"]}
        self.invalid_payload_1 = {"date": str(self.crr_datetime.date()), "time": "20_22"}
        self.invalid_payload_2 = {"delivery_method": "normal"} 
        
    def test_delivery_schedule_model(self):
        delivery = DeliverySchedule.objects.create(**self.delivery_schadule_1)
        self.assertEqual(str(delivery), f"{delivery.id} - {delivery.date} ({delivery.day}) {delivery.time}")
        self.assertEqual(delivery.day, delivery.date.strftime("%A").lower())  

    def test_delivery_schedule_serializer(self):
        self.request.user = self.user_1  
        serializer = DeliveryScheduleSerializer( data=self.delivery_schadule_1, context={"request": self.request})
        self.assertTrue(serializer.is_valid(raise_exception=True)) 
        validated_data = serializer.validated_data
        validated_data["user"] = self.user_1  
        validated_data["shopping_cart"] = self.cart  
        instance = DeliverySchedule.objects.create(**validated_data)  
        self.assertEqual(instance.delivery_method, self.delivery_schadule_1["delivery_method"])
        self.assertEqual(instance.delivery_cost, 35000)
 
    def test_delivery_schedule_view(self):
        self.client.force_authenticate(self.user_1)
        response = self.client.post(self.url, self.valid_payload_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "زمان سفارش با موفقیت ثبت شد.")
        self.assertEqual(response.data["delivery_cost"], 35000)
        
    def test_delivery_schedule_duplicate(self):
        self.client.force_authenticate(self.user_1)
        # First request Successfully create delivery schedule
        response1 = self.client.post(self.url, self.valid_payload_1, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        # Second request with the same user: Should fail due to duplication
        response2 = self.client.post(self.url, self.valid_payload_2, format="json")
        self.assertEqual(response2.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response2.data["error"], "این سفارش قبلا ثبت شده است و یا سفارش فعالی دارید، در صورت داشتن سفارش فعال ابتدا سفارش قبلی خود را تکمیل یا لغو کنید.")
        # Third request with the same user & cart: Should fail due to duplication
        response3 = self.client.post(self.url, self.valid_payload_1, format="json")
        self.assertEqual(response3.status_code, status.HTTP_409_CONFLICT) 
        self.assertIn("error", response2.data)
    
    def test_delivery_schedule_processed_cart(self):
        self.cart.status = "processed"  
        self.cart.save()
        self.client.force_authenticate(self.user_1)
        response = self.client.post(self.url, self.valid_payload_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  
        self.assertEqual(response.data["error"], "سفارش فعالی وجود ندارد.")

    def test_delivery_schedule_missing_method(self):
        self.client.force_authenticate(self.user_1) 
        response = self.client.post(self.url, self.invalid_payload_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) 
        self.assertIn("error", response.data)  

    def test_delivery_schedule_invalid_data(self):
        self.client.force_authenticate(self.user_1) 
        response = self.client.post(self.url, self.invalid_payload_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  
        self.assertIn("error", response.data) 

    def test_delivery_schedule_url(self):
        view = resolve("/products/add_schedule/")
        self.assertEqual(view.func.cls, DeliveryScheduleAPIView)
    

#====================================== Delivery Schedule Change Test ===================================

class DeliveryScheduleChangeTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.delivery_id = 44
        self.url = reverse("change_schedule", kwargs={"delivery_id": self.delivery_id})
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.c1, self.c2, self.c3, self.c4, self.c5, self.c6, self.c7 = create_test_categories()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()
        
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
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.c1, self.c2, self.c3, self.c4, self.c5, self.c6, self.c7 = create_test_categories()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()
        
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
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.c1, self.c2, self.c3, self.c4, self.c5, self.c6, self.c7 = create_test_categories()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()
        
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
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.c1, self.c2, self.c3, self.c4, self.c5, self.c6, self.c7 = create_test_categories()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()
        
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
        self.assertIsInstance(view.func.cls, type)
        
    
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
        self.assertIsInstance(view.func.cls, type)
        
    
#========================================================================================================
