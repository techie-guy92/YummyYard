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
from .models import *
from .serializers import *
from custom_permission import * 


#==================================== admin View ======================================================

def get_product_price(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({"price": product.price})
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
    
def get_cart_price(request, cart_id):
    try:
        cart = ShoppingCart.objects.get(id=cart_id)
        return JsonResponse({"total_amount": cart.total_price}) 
    except ShoppingCart.DoesNotExist:
        return JsonResponse({"error": "Shopping cart not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ==========================================================================================================