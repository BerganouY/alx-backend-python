import logging
from datetime import datetime
from datetime import time
from django.http import HttpResponseForbidden
from django.core.cache import cache
import re


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user if request.user.is_authenticated else "Anonymous"
        logger.info(f"{datetime.now()} - User: {user} - Path: {request.path}")

        response = self.get_response(request)
        return response


class RestrictAccessByTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_time = time.now().time()
        start_time = time(18, 0)  # 6 PM
        end_time = time(21, 0)  # 9 PM

        if start_time <= current_time <= end_time and request.path.startswith('/api/'):
            return HttpResponseForbidden("Chat access restricted between 6PM and 9PM")

        return self.get_response(request)


class OffensiveLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.offensive_words = ['badword1', 'badword2']  # Add your offensive words

    def __call__(self, request):
        if request.method == 'POST' and 'message_body' in request.POST:
            message = request.POST['message_body'].lower()
            if any(word in message for word in self.offensive_words):
                return HttpResponseForbidden("Offensive language detected")

        return self.get_response(request)


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.limit = 5  # 5 requests
        self.window = 60  # 60 seconds

    def __call__(self, request):
        if request.method == 'POST' and request.path.startswith('/api/messages/'):
            ip = request.META.get('REMOTE_ADDR')
            key = f"rate_limit:{ip}"

            current = cache.get(key, 0)
            if current >= self.limit:
                return HttpResponseForbidden("Rate limit exceeded")

            cache.set(key, current + 1, self.window)

        return self.get_response(request)


class RolePermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_paths = ['/api/admin/', '/api/users/']  # Add your admin paths

        if request.path.startswith(tuple(admin_paths)):
            if not request.user.is_authenticated or request.user.role not in ['admin', 'moderator']:
                return HttpResponseForbidden("Insufficient permissions")

        return self.get_response(request)