import json
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from .models import IdempotencyRecord


class IdempotencyService:
    """Serialize requests and commit successful results with their database writes.

    All participating writes must use the default database. The database's unique
    constraint handles concurrent first requests;.
    """

    @staticmethod
    def execute(*, user, scope, key, fingerprint, callback):
        if not isinstance(scope, str) or not scope.strip():
            raise ValueError("scope must be a non-empty operation name")
        with transaction.atomic():
            
            record, created = IdempotencyRecord.objects.select_for_update().get_or_create(
                user=user,
                scope=scope,
                key=key,
                defaults={
                    "request_hash": fingerprint,
                },
            )
            if not created:
                if record.request_hash != fingerprint:
                    return Response(
                        {"detail": "Idempotency-Key was already used with a different request."},
                        status=409,
                    )
                if record.response_status is None:
                    return Response({"detail": "Request is already in progress."}, status=409)
                
                response = Response(
                    record.response_body,
                    status=record.response_status,
                )
                response["Idempotency-Replayed"] = "true"
                return response

            response = callback()
            if not isinstance(response, Response):
                raise TypeError("Idempotency requires a DRF Response.")
            
            if not 200 <= response.status_code < 300:
                transaction.set_rollback(True)
                return response

            # Validate and normalize serializer values before the transaction commits.
            record.response_body = json.loads(JSONRenderer().render(response.data) or b"null")
            record.response_status = response.status_code
            record.request_hash = fingerprint
            record.save(update_fields=['response_status', 'response_body', 'request_hash'])
            response["Idempotency-Replayed"] = "false"
            return response
