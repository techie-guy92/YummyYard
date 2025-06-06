import threading


#======================================== RequestMiddleware ============================================

_thread_local = threading.local()

class RequestMiddleware:
    """Middleware to store request globally for use in models."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_local.request = request  
        response = self.get_response(request)
        return response

def get_request():
    """Helper function to retrieve the current request object."""
    return getattr(_thread_local, "request", None)


#=======================================================================================================