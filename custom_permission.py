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
        """
        Check if the user is authenticated.

        Parameters:
        request (Request): The request object
        view: The view object

        Returns:
        bool: True if the user is authenticated, False otherwise
        """
        return request.user.is_authenticated
    
    def has_object_permission(self, request: Request, view, obj):
        """
        Check if the user has permission to access the object.

        Parameters:
        request (Request): The request object
        view: The view object
        obj: The object to check permissions for

        Returns:
        bool: True if the user has permission, False otherwise
        """
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user or obj.user == request.user


#====================================================================================================