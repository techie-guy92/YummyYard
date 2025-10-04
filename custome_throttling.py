from rest_framework.throttling import UserRateThrottle
from rest_framework.throttling import BaseThrottle
from rest_framework.exceptions import Throttled
from django.core.cache import cache


#======================================== Custom Throttle ===========================================

class CustomThrottle(BaseThrottle):
    """
    A flexible, per-user throttling class for DRF.
    This throttle enforces a simple cooldown period between requests, scoped by a custom identifier.
    It uses Django's cache backend to track request timestamps and blocks repeated access within
    the specified time window.

    Attributes:
        scope (str): A unique identifier for the throttle context (e.g., 'email_change', 'comment_post').
        seconds (int): The cooldown duration in seconds during which repeated requests are blocked.

    Behavior:
        - Authenticated users are throttled individually based on their user ID.
        - Anonymous users bypass throttling (can be extended if needed).
        - If a user is throttled, a localized error message is raised with the remaining wait time.
        - The `wait()` method returns the cooldown duration for DRF's Retry-After header support.

    Example:
        EmailChangeThrottle = CustomThrottle(scope="email_change", seconds=1800)
        throttle_classes = [EmailChangeThrottle]

    Note:
        This class must be subclassed with fixed parameters to be used in DRF's `throttle_classes`.
    """
    def __init__(self, scope: str, seconds: int):
        self.scope = scope
        self.seconds = seconds

    def allow_request(self, request, view):
        if not request.user.is_authenticated:
            return True
        user_id = request.user.pk
        cache_key = f"{self.scope}_throttle_{user_id}"
        if cache.get(cache_key):
            remaining = cache.ttl(cache_key)
            minutes = max(1, (remaining + 59) // 60) 
            raise Throttled(detail=f"لطفاً {minutes} دقیقه دیگر تلاش کنید.")
        cache.set(cache_key, True, self.seconds)
        return True
    
    def wait(self):
        return self.seconds


#====================================================================================================