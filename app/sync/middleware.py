import hmac
import json

import jsonschema

from django.conf import settings
from django.http import JsonResponse
import jsonschema.exceptions

from .schemas import POST_SYNC_OBJECT_SCHEMA


class HMacAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the incoming request and authenticate it using HMAC, if it's not a GET method or /admin/ request.
        """
        if request.method == "GET" or request.path.startswith("/admin/"):
            return self.get_response(request)

        if not request.headers.get("Authorization"):
            return JsonResponse({"detail": "Missing/empty Authorization header"}, status=401)

        request_hmac = request.headers.get("Authorization")

        calculated_hmac = hmac.new(
            key=bytes(settings.SECRET_KEY, "utf-8"),
            msg=request.body,
            digestmod="sha256",
        ).hexdigest()

        # Compare the request's HMAC signature with the calculated HMAC signature
        if request_hmac != calculated_hmac:
            return JsonResponse({"detail": "Invalid HMAC signature hash"}, status=401)

        return self.get_response(request)


class JSONParseValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the incoming request, parse the body as JSON and validates its content, if it contains a body and is
        bound to /sync/ path
        """
        if not request.body or request.path != "/sync/":
            return self.get_response(request)

        try:
            request_data = json.loads(request.body.decode())
            jsonschema.validate(request_data, POST_SYNC_OBJECT_SCHEMA)
            request.POST = request_data
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Malformed JSON data"}, status=400)
        except jsonschema.exceptions.ValidationError:
            return JsonResponse({"detail": "Invalid JSON data"}, status=400)

        return self.get_response(request)
