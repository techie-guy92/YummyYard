class MetricsHostBypassMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/metrics':
            request.META['HTTP_HOST'] = 'localhost'
        return self.get_response(request)
