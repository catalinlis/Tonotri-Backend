from functools import wraps
from uuid import UUID

from rest_framework.exceptions import ValidationError, NotAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .fingerprint import digest, fingerprint
from .services import IdempotencyService


def idempotent(*, scope: str, required=True):
    """Decorate a DRF function view or APIView/ViewSet handler.

    A string scope names the operation, e.g. ``upload_profile_photo``.
    Authentication and permission checks must run before this decorator.
    """
    if not isinstance(scope, str) or not scope.strip():
        raise ValueError("scope must be a non-empty operation name")

    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            request = next((arg for arg in args[:2] if isinstance(arg, Request)), None)
            if request is None:
                request = kwargs.get("request")
            if not isinstance(request, Request):
                raise TypeError("Apply @idempotent to a DRF handler, inside @api_view.")
            if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
                return view(*args, **kwargs)
            key = request.headers.get("Idempotency-Key")
            if key is None and not required:
                return view(*args, **kwargs)
            if not key:
                raise ValidationError({"detail": "Idempotency-Key is required."})
            try:
                key = str(UUID(key))
            except ValueError:
                raise ValidationError({"detail": "Idempotency-Key must be a valid UUID."})
            if not request.user.is_authenticated:
                raise NotAuthenticated()
            # An operation may cover multiple resources; prevent cross-resource replay.
            request_fingerprint = digest([request.method, request.path, fingerprint(request)])
            return IdempotencyService.execute(
                scope=scope,
                key=key,
                fingerprint=request_fingerprint,
                callback=lambda: view(*args, **kwargs),
                user=request.user,
            )
        return wrapped
    return decorate
