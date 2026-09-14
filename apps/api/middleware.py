from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpResponse


def origin_allowed(origin):
    if not origin:
        return False
    allowed = list(getattr(settings, 'CORS_ALLOWED_ORIGINS', None) or [])
    if origin in allowed:
        return True
    if not getattr(settings, 'DEBUG', False):
        return False
    host = (urlparse(origin).hostname or '').lower()
    return host in {'localhost', '127.0.0.1', '10.0.2.2'}


class MobileApiCorsMiddleware:
    """Allow Flutter web / emulator clients to call /api/v1/ and /media/."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/') or request.path.startswith('/media/'):
            if request.method == 'OPTIONS':
                response = HttpResponse()
            else:
                response = self.get_response(request)
            origin = request.headers.get('Origin')
            if origin_allowed(origin):
                response['Access-Control-Allow-Origin'] = origin
                response['Access-Control-Allow-Credentials'] = 'true'
                response['Vary'] = 'Origin'
            elif not origin:
                response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Authorization, Content-Type, Accept, X-Requested-With'
            )
            response['Access-Control-Allow-Private-Network'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            return response
        return self.get_response(request)
