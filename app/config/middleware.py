import threading
import contextvars


#======================================== RequestMiddleware ============================================

_thread_local = threading.local()

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_local.request = request  
        response = self.get_response(request)
        return response

def get_request():
    return getattr(_thread_local, "request", None)


_request_var = contextvars.ContextVar("request_var")  

class AsyncRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    async def __call__(self, request):
        _request_var.set(request)  
        response = await self.get_response(request)  
        return response

async def get_async_request():
    try:
        return _request_var.get(None) 
    except LookupError:
        return None 


#=======================================================================================================