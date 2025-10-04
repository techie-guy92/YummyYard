from rest_framework.throttling import UserRateThrottle
from rest_framework.throttling import BaseThrottle
from rest_framework.exceptions import Throttled
from django.core.cache import cache


#======================================== Custom Throttle ===========================================

class CustomThrottle(BaseThrottle):
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