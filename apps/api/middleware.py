class MobileApiCorsMiddleware:
    """Allow Flutter web / emulator clients to call /api/v1/."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/') or request.path.startswith('/media/'):
            if request.method == 'OPTIONS':
                from django.http import HttpResponse
                response = HttpResponse()
            else:
                response = self.get_response(request)
            origin = request.headers.get('Origin')
            if origin:
                response['Access-Control-Allow-Origin'] = origin
                response['Access-Control-Allow-Credentials'] = 'true'
                response['Vary'] = 'Origin'
            else:
                response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Authorization, Content-Type, Accept, X-Requested-With'
            )
            response['Access-Control-Allow-Private-Network'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            return response
        return self.get_response(request)
