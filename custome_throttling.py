from rest_framework.throttling import UserRateThrottle
from rest_framework.throttling import BaseThrottle
from rest_framework.exceptions import Throttled
from django.core.cache import cache
from logging import getLogger
from utilities import get_client_ip


#======================================== Custom Throttle ===========================================

logger = getLogger(__name__)


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
        - Anonymous users are throttled based on their IP address.
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
        if request.user.is_authenticated:
            identifier = f"user_{request.user.pk}"
        elif request.data.get("email", "").strip():
            email = request.data.get("email", "").lower().strip()
            identifier = f"email_{email}"
        else:
            ip = get_client_ip(request)
            identifier = f"ip_{ip}"

        safe_identifier = identifier or "anonymous"
        cache_key = f"{self.scope}_throttle_{safe_identifier}"
        if cache.get(cache_key):
            remaining = cache.ttl(cache_key)
            minutes = max(1, (remaining + 59) // 60)
            logger.info(f"Throttle triggered for {identifier} on scope '{self.scope}'") 
            raise Throttled(detail=f"لطفاً {minutes} دقیقه دیگر تلاش کنید.")
        cache.set(cache_key, True, self.seconds)
        return True

    def wait(self):
        return self.seconds


#====================================================================================================