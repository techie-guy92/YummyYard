from rest_framework import status, viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from logging import getLogger
from .models import *
from .serializers import *
from custom_permission import CheckOwnershipPermission


#====================================== admin View ===================================================

logger = getLogger(__name__)


def get_product_price(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({"price": product.price})
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=500)
    
    
def get_cart_price(request, cart_id):
    try:
        cart = ShoppingCart.objects.get(id=cart_id)
        return JsonResponse({"total_amount": cart.total_price}) 
    except ShoppingCart.DoesNotExist:
        return JsonResponse({"error": "Shopping cart not found"}, status=404)
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=500)


#====================================== Gategory View ================================================

class CategoryModelViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Category.objects.all().order_by("parent")
    serializer_class = CategorySerializer
    http_method_names = ["get"]
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ["parent"]
    search_fields = ["slug", "parent__name"]


#====================================== Product View =================================================

class ProductModelViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Product.objects.all().order_by("-price")
    serializer_class = ProductSerializer
    http_method_names = ["get"]
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ["category"]
    search_fields = ["slug", "name", "category__name"]


#====================================== Wishlist View ================================================

class WishlistModelViewSet(viewsets.ModelViewSet):
    permission_classes = [CheckOwnershipPermission]
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    http_method_names = ["get", "post", "delete"]
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter]
    search_fields = ["product__name", "user__username"]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
    
    # def perform_create(self, serializer):
    #     serializer.save(user=self.request.user)
    
    @action(detail=False, methods=["delete"], url_path="delete_by_product/(?P<product_id>[0-9]+)")
    def destroy_by_product(self, request, product_id=None):
        wishlist_item = Wishlist.objects.filter(user=request.user, product_id=product_id).first()
        if wishlist_item:
            wishlist_item.delete()
            return Response({"detail": "کالای مورد نظر با موفقیت حذف شد."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "کالای مورد نظر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)


#====================================== ShoppingCart View ============================================

class ShoppingCartAPIView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request = ShoppingCartSerializer,
        responses = {201: "Cart created successfully", 400: "Failed to create cart"}    
    )
    def create(self, request: Request, *args, **kwargs):
        serializer = ShoppingCartSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            cart = serializer.save()
            serialized_cart_items = CartItemSerializer(cart.CartItem_cart.all(), many=True).data
            return Response(
                {
                    "message": "کالاهای شما اضافه شد.", 
                    "cart_id": cart.id, 
                    "cart_items_count": cart.CartItem_cart.count(), 
                    "total_price": cart.total_price,
                    "cart_items": serialized_cart_items, 
                }, 
                status=status.HTTP_201_CREATED
            )
        return Response({"error": serializer.errors, "details": "سبد خرید ایجاد نشد."}, status=status.HTTP_400_BAD_REQUEST)


#====================================== Delivery Schedule View =======================================

class DeliveryScheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=DeliveryScheduleSerializer,
        responses={
            201: "Delivery schedule created successfully",
            400: "No active shopping cart found",
            409: "This order has already been completed",
            500: "An unexpected error occurred",
        },
    )
    def post(self, request):
        customer = request.user
        cart = ShoppingCart.objects.filter(online_customer=customer, status="active").last()
        if not cart:
            return Response({"error": "سفارش فعالی وجود ندارد."}, status=status.HTTP_400_BAD_REQUEST)
        if cart.status == "processed":
            return Response({"error": "شما نمی توانید یک سفارش پردازش شده را ثبت کنید، لطفا یک سبد خرید جدید ایجاد کنید."}, status=status.HTTP_400_BAD_REQUEST)
        order = Order.objects.filter(online_customer=customer, shopping_cart=cart)
        if order.exists():
            return Response({"error": "این سفارش قبلا تکمیل شده است."}, status=status.HTTP_409_CONFLICT)
        delivery_schedule = DeliverySchedule.objects.filter(user=customer, shopping_cart=cart).first()
        if delivery_schedule:
            return Response(
                {
                    "error": "این ارسال سفارش قبلا ثبت شده است.",
                    "delivery_id": delivery_schedule.id,
                    "delivery_date": delivery_schedule.date,
                    "delivery_time": delivery_schedule.time,
                }, 
                status=status.HTTP_409_CONFLICT,
            )
        
        data = request.data.copy()
        serializer = DeliveryScheduleSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            try:
                delivery_data = serializer.validated_data
                delivery = DeliverySchedule(user=customer, shopping_cart=cart, **delivery_data)
                delivery.save() 
                return Response(
                    {
                        "message": "زمان سفارش با مئفقیت ثبت شد.",
                        "delivery_id": delivery.id,
                        "delivery_cost": delivery.delivery_cost,
                        "delivery_date": delivery.date,
                        "delivery_time": delivery.time,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except ValidationError as error:
                return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as error:
                logger.error(f"Unexpected error occurred in DeliveryScheduleAPIView for user {customer.username}: {error}")
                return Response({"error": f"An unexpected error occurred: {error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"error": serializer.errors, "details": "Validation failed."}, status=status.HTTP_400_BAD_REQUEST)


#====================================== Order View ===================================================

class OrderAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request = OrderSerializer,
        responses = {
            201: "An order has been successfully registered.",
            400: "Something went wrong. Please check your input.",
            500: "An internal error occurred. Please try again later."
        }
    )
    def post(self, request):
        try:
            serializer = OrderSerializer(data=request.data, context={"request": request})
            if serializer.is_valid():
                order = serializer.save()
                return Response(
                    {"message": "سفارش شما با موفقیت ثبت شد و آماده پرداخت است.", "Order_data": OrderSerializer(order).data}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({"error": f"An unexpected error occurred: {str(error)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#====================================== Transaction View =============================================

# Note: This class is a placeholder for future integration with a payment gateway. 
# It is currently defined as a sample and does not include the full implementation.

class TransactionModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    http_method_names = ["post"]
    
    def perform_create(self, serializer):
        user = self.request.user
        order = serializer.validated_data["order"]
        amount = order.amount_payable
        # Simulated gateway response 
        gateway_response = {
            "payment_id": "XYZ12345",
            "status": "successful",
            "amount": amount,
        }
        if gateway_response["status"] != "successful":
            raise ValidationError("پرداخت ناموفق، لطفا دوباره تلاش کنید.")
        serializer.save(
            user=user, 
            amount=gateway_response["amount"],
            payment_id=gateway_response["payment_id"],
            is_successful=True
        )


#====================================== Delivery View ================================================

class DeliveryAPIView(APIView):
    permission_classes = [CheckOwnershipPermission]
    
    @extend_schema(
        request = DeliverySerializer,
        responses = {
            200: "Delivery status updated successfully.",
            400: "Invalid request data.",
            500: "Internal server error."
        }
    )
    def put(self, request):
        try:
            delivery = Delivery.objects.filter(order__online_customer=request.user, order__status="successful").last()
            if not delivery:
                return Response({"error": "سفارش پرداخت شده که تکمیل نشده باشد وجود ندارد."}, status=status.HTTP_404_NOT_FOUND)
            serializer = DeliverySerializer(data=request.data, instance=delivery, partial=True, context={"request": request})
            if serializer.is_valid():
                updated_delivery = serializer.save()
                return Response({"message": "سفارش شما با موفقیت تکمیل شد.", "delivery_data": DeliverySerializer(updated_delivery).data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
          return Response({"error": f"An unexpected error occurred: {str(error)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
#====================================== UserView View ================================================

class UserViewModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = UserView.objects.all()
    serializer_class = UserViewSerializer
    http_method_names = ["get", "post"]
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        product_id = self.kwargs.get("product_id")
        if product_id:
            return self.queryset.filter(user=self.request.user, product_id=product_id)
        return self.queryset.filter(user=self.request.user)


#====================================== Rating View ==================================================

class RatingModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    http_method_names = ["get", "post"]
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter]
    search_fields = ["id", "user__username"]

    def perform_create(self, serializer):
        product_id = self.kwargs.get("product_id")
        if not product_id:
            product_id = self.request.data.get("product")
        product = get_object_or_404(Product, id=product_id)
        serializer.save(user=self.request.user, product=product)


# ====================================================================================================