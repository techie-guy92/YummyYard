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
from custom_permission import * 


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
    permission_classes = [IsAuthenticated]
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
            return Response({"detail": "Wishlist item deleted successfully."}, status=204)
        return Response({"detail": "Wishlist item not found."}, status=404)


#====================================== ShoppingCart View ============================================

class ShoppingCartAPIView(APIView):
    pass


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