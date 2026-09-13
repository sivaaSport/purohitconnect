import json
from functools import wraps

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import MobileAuthToken


def json_ok(payload=None, status=200):
    data = {'success': True}
    if payload:
        data.update(payload)
    return JsonResponse(data, status=status)


def json_error(message, status=400, **extra):
    payload = {'success': False, 'error': message}
    payload.update(extra)
    return JsonResponse(payload, status=status)


def parse_json(request):
    if not request.body:
        return {}
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _extract_token(request):
    header = request.META.get('HTTP_AUTHORIZATION', '')
    if header.startswith('Bearer '):
        return header[7:].strip()
    return request.GET.get('token') or request.POST.get('token') or ''


def api_auth_required(view):
    @csrf_exempt
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        key = _extract_token(request)
        if not key:
            return json_error('Authentication required', status=401)
        try:
            token = MobileAuthToken.objects.select_related('user').get(key=key)
        except MobileAuthToken.DoesNotExist:
            return json_error('Invalid or expired session', status=401)
        if not token.user.is_active:
            return json_error('Account is disabled', status=403)
        token.touch()
        request.user = token.user
        request.mobile_token = token
        return view(request, *args, **kwargs)

    return wrapper


def api_public(view):
    @csrf_exempt
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        key = _extract_token(request)
        request.mobile_token = None
        if key:
            try:
                token = MobileAuthToken.objects.select_related('user').get(key=key)
                if token.user.is_active:
                    token.touch()
                    request.user = token.user
                    request.mobile_token = token
            except MobileAuthToken.DoesNotExist:
                pass
        return view(request, *args, **kwargs)

    return wrapper
