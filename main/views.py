from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from django.http import JsonResponse
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


#====================================== Wishlist View ================================================

class WishlistModelViewSet(viewsets.ModelViewSet):
    permission_classes = [CheckOwnershipPermission]
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    http_method_names = ["get", "post", "delete"]
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter]
    search_fields = ["user__username", "user__email", "product__name"]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=["delete"], url_path="delete_by_product/(?P<product_id>[0-9]+)")
    def destroy_by_product(self, request, product_id=None):
        wishlist_item = Wishlist.objects.filter(user=request.user, product_id=product_id).first()
        if wishlist_item:
            wishlist_item.delete()
            print("Wishlist item found and being deleted.")
            return Response({"detail": "Wishlist item deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        print("Wishlist item not found.")
        return Response({"detail": "Wishlist item not found."}, status=status.HTTP_404_NOT_FOUND)


#====================================== ShoppingCart View ============================================

class ShoppingCartAPIView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request = ShoppingCartSerializer,
        responses = {201: "Cart created successfully", 400: "Failed to create cart"}    
    )
    def create(self, request, *args, **kwargs):
        serializer = ShoppingCartSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            cart = serializer.save()
            return Response(
                {
                    "message": "کالاهای شما اضافه شد.", 
                    "cart_id": cart.id, 
                    "total_price": cart.total_price,
                }, 
                status=status.HTTP_201_CREATED
        )
        return Response(
            {
                "error": serializer.errors, 
                "details": "Failed to create shopping cart."
            }, 
            status=status.HTTP_400_BAD_REQUEST
        )


#====================================== Delivery Schedule View =======================================

class DeliveryScheduleAPIView(APIView):
    pass


#====================================== Order Serializer =============================================

class OrderAPIView(APIView):
    pass


#====================================== Transaction View =============================================

class TransactionModelViewSet(viewsets.ModelViewSet):
    pass


#====================================== UserView View ================================================

class UserViewModelViewSet(viewsets.ModelViewSet):
    pass


#====================================== Rating View ==================================================

class RatingModelViewSet(viewsets.ModelViewSet):
    pass


# ====================================================================================================