import os
os.environ["DJANGO_SETTINGS_MODULES"] = "config.settings"
import django
django.setup()

from rest_framework.test import APITestCase, APIClient, APIRequestFactory
from rest_framework import status
from django.urls import resolve, reverse
from django.utils.timezone import localtime, now, make_aware
from datetime import timedelta, datetime
from .models import *
from .serializers import *
from .views import *
from .urls import *
from utilities.users_constant import *
from utilities.products_constant import *
from utilities.utilities import create_test_users, create_test_categories, create_test_products


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
        expected_total = sum(item["quantity"] * Product.objects.get(id=item["product"]).price for item in self.cart_2["cart_items"])
        serializer = ShoppingCartSerializer(data=self.cart_2, context={"request": self.request})
        self.assertTrue(serializer.is_valid(raise_exception=True))
        serializer.save()
        ser_data = serializer.data
        self.assertEqual(ser_data["total_price"], expected_total)   
    
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
        self.crr_date = self.crr_datetime.date() + timedelta(days=1)
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()
        self.increment_stock_1 = Warehouse.objects.create(product=self.p1, stock=50)
        self.increment_stock_2 = Warehouse.objects.create(product=self.p2, stock=50)
        self.increment_stock_3 = Warehouse.objects.create(product=self.p3, stock=50)
        self.cart = ShoppingCart.objects.create(online_customer=self.user_1)
        self.cart_item_1 = CartItem.objects.create(cart=self.cart, product=self.p1, quantity=2)
        self.cart_item_2 = CartItem.objects.create(cart=self.cart, product=self.p2, quantity=3)
        self.cart.save()
        self.delivery_schadule_1 = {"user": self.user_1, "shopping_cart": self.cart, "delivery_method": "normal", "date": self.crr_date, "time": "20_22"}
        self.delivery_schadule_2 = {"user": self.user_1, "shopping_cart": self.cart, "delivery_method": "normal", "date": self.crr_date, "time": "8_10"}
        self.valid_payload_1 = {"delivery_method": self.delivery_schadule_1["delivery_method"], "date": str(self.delivery_schadule_1["date"]), "time": self.delivery_schadule_1["time"]}
        self.valid_payload_2 = {"delivery_method": self.delivery_schadule_2["delivery_method"], "date": str(self.delivery_schadule_2["date"]), "time": self.delivery_schadule_2["time"]}
        self.invalid_payload_1 = {"date": str(self.crr_date), "time": "20_22"}
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
    
    def tearDown(self):
        CartItem.objects.all().delete()  
        ShoppingCart.objects.all().delete()  
        DeliverySchedule.objects.all().delete() 
        
        
#====================================== Delivery Schedule Change Test ===================================

class DeliveryScheduleChangeTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.crr_datetime = localtime(now())
        self.the_day_after_tommorow = self.crr_datetime.date() + timedelta(days=2)
        self.three_day_ahead = self.crr_datetime.date() + timedelta(days=3)
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()
        self.increment_stock_1 = Warehouse.objects.create(product=self.p1, stock=50)
        self.increment_stock_2 = Warehouse.objects.create(product=self.p2, stock=50)
        self.increment_stock_3 = Warehouse.objects.create(product=self.p3, stock=50)
        self.cart = ShoppingCart.objects.create(online_customer=self.user_1)
        self.cart_item_1 = CartItem.objects.create(cart=self.cart, product=self.p1, quantity=2)
        self.cart_item_2 = CartItem.objects.create(cart=self.cart, product=self.p2, quantity=3)
        self.cart.save()
        self.delivery_schadule_1 = {"user": self.user_1, "shopping_cart": self.cart, "delivery_method": "normal", "date": self.the_day_after_tommorow, "time": "20_22"}
        self.delivery_schadule_2 = {"date": self.three_day_ahead, "time": "14_16"}
        self.invalid_schadule = {"date": self.three_day_ahead, "time": "22_24"} 
        self.delivery_schadule = DeliverySchedule.objects.create(**self.delivery_schadule_1)
        self.url = reverse("change_schedule", kwargs={"delivery_id": self.delivery_schadule.id})
        
    def test_delivery_schedule_change_serializer(self):
        serializer = DeliveryScheduleChangeSerializer(instance=self.delivery_schadule, data=self.delivery_schadule_2)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        serializer.save()
        updated_instance = DeliverySchedule.objects.get(id=self.delivery_schadule.id)
        self.assertEqual(str(updated_instance.date), str(self.three_day_ahead))
        
    def test_delivery_schedule_invalid_time_format(self):
        serializer = DeliveryScheduleChangeSerializer(instance=self.delivery_schadule, data=self.invalid_schadule)
        self.assertFalse(serializer.is_valid())  
        self.assertIn("time", serializer.errors)  
        self.assertEqual(serializer.errors["time"][0], '"22_24" is not a valid choice.') 

    def test_delivery_schedule_change_view(self):
        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(self.url, self.delivery_schadule_2, format="json")
        expected_message = f"زمان ارسال سفارش شما با موفقیت به {self.three_day_ahead} در {self.delivery_schadule_2['time']} تغییر کرد."
        updated_instance = DeliverySchedule.objects.get(id=self.delivery_schadule.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)  
        self.assertEqual(response.data["message"], expected_message)
        self.assertEqual(str(updated_instance.date), str(self.three_day_ahead))  
        self.assertEqual(updated_instance.time, self.delivery_schadule_2["time"])  

    def test_delivery_schedule_change_url(self):
        view = resolve(f"/products/change_schedule/{self.delivery_schadule.id}/")
        self.assertEqual(view.func.cls, DeliveryScheduleChangeAPIView)
    
    def tearDown(self):
        CartItem.objects.all().delete()  
        ShoppingCart.objects.all().delete()  
        DeliverySchedule.objects.all().delete() 
        
        
#====================================== Order Test ======================================================

class OrderTest(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.url = reverse("complete_order")
        self.request = self.factory.post(self.url)
        self.crr_datetime = localtime(now())
        self.four_day_ahead = make_aware(datetime.combine(self.crr_datetime.date() + timedelta(days=4), datetime.min.time()))
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()
        self.increment_stock_1 = Warehouse.objects.create(product=self.p1, stock=150)
        self.increment_stock_2 = Warehouse.objects.create(product=self.p2, stock=150)
        self.increment_stock_3 = Warehouse.objects.create(product=self.p3, stock=150)
        self.increment_stock_4 = Warehouse.objects.create(product=self.p4, stock=150)
        self.cart_1 = ShoppingCart.objects.create(online_customer=self.user_1)
        self.cart_2 = ShoppingCart.objects.create(online_customer=self.user_2)  
        self.cart_item_1 = CartItem.objects.create(cart=self.cart_1, product=self.p1, quantity=2)
        self.cart_item_2 = CartItem.objects.create(cart=self.cart_1, product=self.p2, quantity=3)
        self.cart_item_3 = CartItem.objects.create(cart=self.cart_2, product=self.p3, quantity=2)
        self.cart_item_4 = CartItem.objects.create(cart=self.cart_2, product=self.p2, quantity=5)
        self.cart_1.save()
        self.cart_2.save()
        self.delivery_schedule_1 = DeliverySchedule.objects.create(user=self.user_1, shopping_cart=self.cart_1, delivery_method="normal", date=self.four_day_ahead, time="20_22")
        self.delivery_schedule_2 = DeliverySchedule.objects.create(user=self.user_2, shopping_cart=self.cart_2, delivery_method="fast", date=self.four_day_ahead, time="20_22") 
        self.coupon = Coupon.objects.create(code="DISCOUNT15", discount_percentage=15, max_usage=3, valid_from=self.crr_datetime, valid_to=self.four_day_ahead)
        self.coupon.is_active = True  
        self.coupon.save()
        self.coupon.refresh_from_db()
        self.order_1 = {"online_customer": self.user_1, "shopping_cart": self.cart_1, "delivery_schedule": self.delivery_schedule_1, "payment_method": "online"}
        self.order_2 = {"online_customer": self.user_2.id, "shopping_cart": self.cart_2.id, "delivery_schedule": self.delivery_schedule_2.id, "payment_method": "online"} 
        
    # @classmethod
    # def setUpTestData(cls):
    #     cls.factory = APIRequestFactory()
    #     cls.client = APIClient()
    #     cls.url = reverse("complete_order")
    #     cls.request = cls.factory.post(cls.url)
    #     cls.crr_datetime = localtime(now())
    #     cls.four_day_ahead = make_aware(datetime.combine(cls.crr_datetime.date() + timedelta(days=4), datetime.min.time()))
    #     cls.user_1, cls.user_2, cls.user_3, cls.user_4 = create_test_users()
    #     cls.p1, cls.p2, cls.p3, cls.p4, cls.p5, cls.p6, cls.p7, cls.p8 = create_test_products()
    #     cls.increment_stock_1 = Warehouse.objects.create(product=cls.p1, stock=150)
    #     cls.increment_stock_2 = Warehouse.objects.create(product=cls.p2, stock=150)
    #     cls.increment_stock_3 = Warehouse.objects.create(product=cls.p3, stock=150)
    #     cls.increment_stock_4 = Warehouse.objects.create(product=cls.p4, stock=150)
    #     cls.cart_1 = ShoppingCart.objects.create(online_customer=cls.user_1)
    #     cls.cart_2 = ShoppingCart.objects.create(online_customer=cls.user_2)
    #     cls.cart_item_1 = CartItem.objects.create(cart=cls.cart_1, product=cls.p1, quantity=2)
    #     cls.cart_item_2 = CartItem.objects.create(cart=cls.cart_1, product=cls.p2, quantity=3)
    #     cls.cart_item_3 = CartItem.objects.create(cart=cls.cart_2, product=cls.p3, quantity=2)
    #     cls.cart_item_4 = CartItem.objects.create(cart=cls.cart_2, product=cls.p2, quantity=5)
    #     cls.cart_1.save()
    #     cls.cart_2.save()
    #     cls.delivery_schedule_1 = DeliverySchedule.objects.create(user=cls.user_1, shopping_cart=cls.cart_1, delivery_method="normal", date=cls.four_day_ahead, time="20_22")
    #     cls.delivery_schedule_2 = DeliverySchedule.objects.create(user=cls.user_2, shopping_cart=cls.cart_2, delivery_method="fast", date=cls.four_day_ahead, time="20_22")
    #     cls.coupon = Coupon.objects.create(code="DISCOUNT15", discount_percentage=15, max_usage=3, valid_from=cls.crr_datetime, valid_to=cls.four_day_ahead)
    #     cls.coupon.is_active = True  
    #     cls.coupon.save()
    #     cls.coupon.refresh_from_db()
    #     cls.order_1 = {"online_customer": cls.user_1, "shopping_cart": cls.cart_1, "delivery_schedule": cls.delivery_schedule_1, "payment_method": "online"}
    #     cls.order_2 = {"online_customer": cls.user_2.id, "shopping_cart": cls.cart_2.id, "delivery_schedule": cls.delivery_schedule_2.id, "payment_method": "online"}
     
    def test_order_model(self):
        order = Order.objects.create(**self.order_1)
        self.assertEqual(str(order), f"Order {order.id} by {self.user_1} ({order.get_order_type_display()})")
    
    def test_order_serializer(self):
        self.request.user = self.user_1
        serializer = OrderSerializer(data=self.order_1, context={"request": self.request})
        self.assertTrue(serializer.is_valid(raise_exception=True))
        serializer.save()
        ser_data = serializer.data
        self.assertEqual(ser_data["payment_method"], self.order_1["payment_method"])
        self.assertEqual(ser_data["status"], "waiting")
        self.assertEqual(ser_data["total_amount"], (self.cart_1.total_price + self.delivery_schedule_1.delivery_cost))
    
    def test_order_view(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(self.url, self.order_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "سفارش شما با موفقیت ثبت شد و آماده پرداخت است.")
        
    def test_order_view_with_discount(self):
        self.client.force_authenticate(user=self.user_2)
        expected_total_amount = (self.cart_2.total_price + self.delivery_schedule_2.delivery_cost) 
        expected_discount = expected_total_amount * (self.coupon.discount_percentage / 100)        
        self.order_2["discount"] = self.coupon.code
        expected_payable = expected_total_amount - expected_discount
        response = self.client.post(self.url, self.order_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["Order_data"]["total_amount"], expected_total_amount)
        self.assertEqual(response.data["Order_data"]["discount_applied"], expected_discount)
        self.assertEqual(response.data["Order_data"]["amount_payable"], expected_payable)
    
    def test_order_view_invalid_discount(self):
        self.client.force_authenticate(user=self.user_2)
        invalid_coupon_code = "INVALIDCOD"
        self.order_2["discount"] = invalid_coupon_code
        response = self.client.post(self.url, self.order_2, format="json")
        print("Full response error:", response.data)
        self.assertIn("کد تخفیف اشتباه است.", response.data["error"]) 
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_url(self):
        view = resolve("/products/complete_order/")
        self.assertEqual(view.func.cls, OrderAPIView)
    
    def tearDown(self):
        CartItem.objects.all().delete()  
        ShoppingCart.objects.all().delete()  
        DeliverySchedule.objects.all().delete() 
        Coupon.objects.all().delete() 


#====================================== Order Cancellation Test =========================================

class OrderCancellationTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.crr_datetime = localtime(now())
        self.crr_date = self.crr_datetime.date() + timedelta(days=1)
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()
        self.increment_stock_1 = Warehouse.objects.create(product=self.p1, stock=150)
        self.increment_stock_2 = Warehouse.objects.create(product=self.p2, stock=150)
        self.increment_stock_3 = Warehouse.objects.create(product=self.p3, stock=150)
        self.increment_stock_4 = Warehouse.objects.create(product=self.p4, stock=150)
        self.cart_1 = ShoppingCart.objects.create(online_customer=self.user_1)
        self.cart_2 = ShoppingCart.objects.create(online_customer=self.user_2)  
        self.cart_item_1 = CartItem.objects.create(cart=self.cart_1, product=self.p1, quantity=2)
        self.cart_item_2 = CartItem.objects.create(cart=self.cart_1, product=self.p2, quantity=3)
        self.cart_item_3 = CartItem.objects.create(cart=self.cart_2, product=self.p3, quantity=2)
        self.cart_item_4 = CartItem.objects.create(cart=self.cart_2, product=self.p2, quantity=5)
        self.cart_1.save()
        self.cart_2.save()
        self.delivery_schedule_1 = DeliverySchedule.objects.create(user=self.user_1, shopping_cart=self.cart_1, delivery_method="normal", date=self.crr_date, time="20_22")
        self.delivery_schedule_2 = DeliverySchedule.objects.create(user=self.user_2, shopping_cart=self.cart_2, delivery_method="fast", date=self.crr_date, time="20_22") 
        self.order_data = {"online_customer": self.user_1, "shopping_cart": self.cart_1, "delivery_schedule": self.delivery_schedule_1, "payment_method": "online"}
        self.order_1 = Order.objects.create(**self.order_data)
        self.url = reverse("cancel_order", kwargs={"order_id": self.order_1.id})
    
    def test_order_cancellation_serializer(self):
        serializer = OrderCancellationSerializer(instance=self.order_1)
        ser_data = serializer.data
        self.assertEqual(ser_data["status"], self.order_1.status)
        serializer.update(self.order_1, validated_data={})
        self.assertEqual(self.order_1.status, "canceled")  
        self.assertEqual(self.order_1.shopping_cart.status, "abandoned")
        
    def test_cannot_cancel_shipped_order(self):
        self.order_1.status = "shipped"
        self.order_1.save()
        serializer = OrderCancellationSerializer(instance=self.order_1)
        with self.assertRaises(serializers.ValidationError) as error:
            serializer.update(self.order_1, validated_data={})
        self.assertEqual(str(error.exception.detail[0]), "سفارش تکمیل شده یا ارسال شده نمیتواند لغو شود.") 
    
    # def test_cannot_cancel_close_to_delivery(self):
    #     self.order_1.delivery_schedule.date = self.crr_datetime.date()
    #     valid_time_slots = [time[0] for time in DeliverySchedule.TIMES] 
    #     next_valid_time = next((slot for slot in valid_time_slots if int(slot.split("_")[0]) >= self.crr_datetime.hour + 2), None)  
    #     if next_valid_time:
    #         self.order_1.delivery_schedule.time = next_valid_time  
    #     else:
    #         raise ValueError("No valid time slots available for testing!")
    #     self.order_1.delivery_schedule.save()
    #     serializer = OrderCancellationSerializer(instance=self.order_1)
    #     with self.assertRaises(serializers.ValidationError) as error:
    #         serializer.update(self.order_1, validated_data={})
    #     self.assertEqual(str(error.exception.detail[0]), "لغو سفارش کمتر از دو ساعت به ارسال امکان پذیر نیست.")    
            
    # def test_order_cancellation_view_invalid_time(self):
    #     self.order_1.delivery_schedule.date = self.crr_datetime.date()
    #     adjusted_hour = self.crr_datetime.hour + 1
    #     if adjusted_hour % 2 != 0:
    #         adjusted_hour += 1  
    #     next_time_slot = adjusted_hour + 2 if adjusted_hour % 2 == 0 else adjusted_hour + 3
    #     if next_time_slot > 20: 
    #         next_time_slot = 8
    #     self.order_1.delivery_schedule.time = f"{adjusted_hour}_{next_time_slot}"
    #     self.order_1.delivery_schedule.save()
    #     self.client.force_authenticate(user=self.user_1)
    #     response = self.client.put(self.url, format="json")
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn("لغو سفارش کمتر از دو ساعت به ارسال امکان پذیر نیست.", response.data["error"])
    
    # def test_order_cancellation_view_invalid_time(self):
    #     self.order_1.delivery_schedule.date = self.crr_datetime.date()
    #     min_valid_hour = max(self.crr_datetime.hour + 4, 8) 
    #     valid_slots = [8, 10, 12, 14, 16, 18, 20]
    #     next_valid_slots = [slot for slot in valid_slots if slot >= min_valid_hour]
    #     selected_hour = next_valid_slots[0] if next_valid_slots else 8  
    #     next_slot_index = valid_slots.index(selected_hour) + 1
    #     next_time_slot = valid_slots[next_slot_index] if next_slot_index < len(valid_slots) else 8  
    #     self.order_1.delivery_schedule.time = f"{selected_hour}_{next_time_slot}"
    #     self.order_1.delivery_schedule.save()
    #     self.client.force_authenticate(user=self.user_1)
    #     response = self.client.put(self.url, format="json")
    #     print(f"Response status code: {response.status_code}, Response data: {response.data}")  
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn("لغو سفارش کمتر از دو ساعت به ارسال امکان پذیر نیست.", response.data["error"])
    
    def test_order_cancellation_view(self):
        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(self.url, format="json")
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(response.data["message"], "سفارش با موفقیت لغو شد.")
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn("لغو سفارش کمتر از دو ساعت به ارسال امکان پذیر نیست.", response.data["error"])
        else:
            self.fail(f"Unexpected response status: {response.status_code}")

    def test_order_cancellation_url(self):
        view = resolve(f"/products/cancel_order/{self.order_1.id}/")
        self.assertEqual(view.func.cls, OrderCancellationAPIView)
    
    def tearDown(self):
        CartItem.objects.all().delete()  
        ShoppingCart.objects.all().delete()  
        DeliverySchedule.objects.all().delete() 

    
#====================================== Delivery Test ===================================================

class DeliveryTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("complete_delivery")
        self.crr_datetime = localtime(now())
        self.five_day_ahead = self.crr_datetime.date() + timedelta(days=5)
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8 = create_test_products()
        self.increment_stock_1 = Warehouse.objects.create(product=self.p1, stock=150)
        self.increment_stock_2 = Warehouse.objects.create(product=self.p2, stock=150)
        self.increment_stock_3 = Warehouse.objects.create(product=self.p3, stock=150)
        self.increment_stock_4 = Warehouse.objects.create(product=self.p4, stock=150)
        self.cart_1 = ShoppingCart.objects.create(online_customer=self.user_1)
        self.cart_2 = ShoppingCart.objects.create(online_customer=self.user_2)  
        self.cart_item_1 = CartItem.objects.create(cart=self.cart_1, product=self.p1, quantity=2)
        self.cart_item_2 = CartItem.objects.create(cart=self.cart_1, product=self.p2, quantity=3)
        self.cart_item_3 = CartItem.objects.create(cart=self.cart_2, product=self.p3, quantity=2)
        self.cart_item_4 = CartItem.objects.create(cart=self.cart_2, product=self.p2, quantity=5)
        self.cart_1.save()
        self.cart_2.save()
        self.delivery_schedule_1 = DeliverySchedule.objects.create(user=self.user_1, shopping_cart=self.cart_1, delivery_method="normal", date=self.five_day_ahead, time="20_22")
        self.delivery_schedule_2 = DeliverySchedule.objects.create(user=self.user_2, shopping_cart=self.cart_2, delivery_method="fast", date=self.five_day_ahead, time="20_22") 
        self.order_data_1 = {"online_customer": self.user_1, "shopping_cart": self.cart_1, "delivery_schedule": self.delivery_schedule_1, "payment_method": "online"}
        self.order_data_2 = {"online_customer": self.user_2, "shopping_cart": self.cart_2, "delivery_schedule": self.delivery_schedule_2, "payment_method": "online"}
        self.order_1 = Order.objects.create(**self.order_data_1)
        self.order_2 = Order.objects.create(**self.order_data_2)
        self.transaction_1 = Transaction.objects.create(user=self.user_1, order=self.order_1, amount=self.order_1.amount_payable, payment_id="341298543212", is_successful=True)
        self.transaction_invalid = Transaction.objects.create(user=self.user_2, order=self.order_2, amount=self.order_2.amount_payable, payment_id="123456789", is_successful=False)
        self.delivery_1 = Delivery.objects.filter(order=self.order_1).first()
        self.transaction_1.refresh_from_db()
        self.delivery_1.refresh_from_db()
        self.tracking_code = {"order": self.delivery_1.order.id, "tracking_code": self.delivery_1.tracking_id}
        self.tracking_code_invalid = {"order": self.delivery_1.order.id, "tracking_code": "INVALID_CODE"}
        
    def test_transaction_model(self):
        self.assertEqual(str(self.transaction_1), f"{self.transaction_1.payment_id}")
    
    def test_delivery_model(self):
        self.assertEqual(str(self.delivery_1), f"Delivery for Order {self.delivery_1.order.id}")
        self.assertIsNotNone(self.delivery_1)  
        self.assertEqual(self.delivery_1.status, "pending")  

    def test_failed_transaction_does_not_create_delivery(self):
        delivery = Delivery.objects.filter(order=self.order_2).first()
        self.assertIsNone(delivery)  

    def test_delivery_serializer(self):
        serializer = DeliverySerializer(instance=self.delivery_1, data=self.tracking_code)  
        self.assertTrue(serializer.is_valid(raise_exception=True))  
        serializer.save()
        ser_data = serializer.data
        self.assertEqual(ser_data["status"], "delivered")

    def test_delivery_view(self):
        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(self.url, self.tracking_code, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "سفارش شما با موفقیت تکمیل شد.")
        self.assertEqual(response.data["delivery_data"]["status"], "delivered")
        
    def test_delivery_view_invalid_code(self):
        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(self.url, self.tracking_code_invalid, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("کد وارد شده صحیح نمی باشد.", str(response.data["tracking_code"][0]))  

    def test_delivery_url(self):
        view = resolve("/products/complete_delivery/")
        self.assertEqual(view.func.cls, DeliveryAPIView)
    
    def tearDown(self):
        CartItem.objects.all().delete()  
        ShoppingCart.objects.all().delete()  
        DeliverySchedule.objects.all().delete() 
        Transaction.objects.all().delete() 
        Delivery.objects.all().delete() 
        

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
