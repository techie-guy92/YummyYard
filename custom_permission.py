from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
import logging


#======================================== User Check Out ============================================

logger = logging.getLogger(__name__)


class CheckOwnershipPermission(BasePermission):
    """
    Custom permission to check ownership of the resource.

    Methods:
    has_permission(self, request, view): Checks if the user is authenticated
    has_object_permission(self, request, view, obj): Checks if the user owns the object or has the right permissions
    """   
    def has_permission(self, request: Request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request: Request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user or getattr(obj, "user", None) == request.user


#====================================================================================================