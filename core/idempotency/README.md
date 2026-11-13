# Shared idempotency

Apply the migration with `python manage.py migrate` before enabling this decorator.
The Django app is registered as `idempotency`; its shared table is
`idempotency_idempotencyrecord`.

Each record links to the authenticated user via `user` (reverse relation:
`user.idempotency_records`). The decorator requires an authenticated user.
Deleting a user also deletes their idempotency records. Direct service callers
can supply the user with `IdempotencyService.execute(..., user=user)`.

## Usage

Decorate the HTTP handler of an authenticated DRF APIView or ViewSet:

```python
from core.idempotency.decorators import idempotent
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class CreateItemView(APIView):
    permission_classes = [IsAuthenticated]

    @idempotent(scope="create_item")
    def post(self, request):
        item = create_item(request.user, request.data)
        return Response({"id": item.pk}, status=201)
```

For a function view, place `@idempotent(scope="operation_name")` **below** `@api_view` and permission decorators so authentication and authorization run on every request, including replays. Do not decorate `dispatch` or `as_view`.

`POST /api/media/images/` uses this decorator and requires `Idempotency-Key`.
Its operation scope is `upload_image`. Use `@idempotent(scope="upload_profile_photo")`
for a profile photo handler. Named scopes are stored verbatim and remain isolated
by user. Reusing a key across paths or methods within one named scope returns 409.
Choose a distinct name for each logical operation. Scope is required and must be
a non-empty string. It is stored verbatim; there is no automatic scope generation.
The shared decorator supports video uploads too; this repository does not yet
define a video endpoint. Apply it to that endpoint's upload handler when added.

Clients send a new `Idempotency-Key` for each logical operation and reuse it for
retries. Keys must be valid UUIDs (for example, generated with `uuid.uuid4()`).
UUIDs are normalized before storage in the `key_hash` UUID field, so equivalent
UUID spellings share the same record. Missing/empty keys and invalid UUIDs return
400. The header is required by default; `required=False` allows requests without
the header to execute normally, but still rejects empty or invalid supplied keys.
GET, HEAD and OPTIONS bypass the service.

## Contract

Request fingerprinting is shared through
`from core.idempotency.fingerprint import fingerprint`. Call `fingerprint(request)`
when invoking the service directly; the decorator already does this. Request
fingerprints use the canonical `digest` helper. Client keys are stored as UUIDs,
without hashing, despite the retained `key_hash` field name.

- Supports synchronous DRF handlers with JSON, multipart/form-data and
  application/x-www-form-urlencoded bodies and DRF `Response` objects.
  Streaming responses and responses setting cookies are not supported.
  Unsupported request content types return 415 before execution;
  unsupported responses raise an error and roll back database writes.
- Keys are isolated by authenticated user and operation name, with method and path
  checked by the fingerprint. Scopes are stored as plain text; client keys are
  UUIDs. Anonymous requests with an idempotency key return 403.
- The fingerprint includes parsed JSON and query parameters.
  JSON object key order is ignored; array and repeated query
  value order is significant. If other headers affect behavior, include them in
  the shared fingerprint function.
- Multipart fingerprints include all repeated fields and files, preserving their
  value order. Files include their name, MIME type, size and SHA-256 content hash.
  Changing any of these changes the fingerprint. Multipart boundaries and field
  name order do not affect it. Files are read in 64 KB chunks and their original
  stream positions restored before the handler executes, including disk uploads.
  A retry must still upload and hash its file before a stored result can replay.
  Endpoint serializers remain responsible for allowed file types and sizes.
- The same key with a changed fingerprint returns 409 until expiry. Successful
  2xx responses are replayed with their JSON body and status. Handler-specific
  response headers are not stored or replayed.
  `Idempotency-Replayed` is `false` on execution and `true` on replay.
- Non-2xx responses and exceptions roll back the handler's database writes and
  do not retain a result. The client can retry the same key. Raised DRF exceptions
  are still processed by DRF's normal exception handler.
- Retention defaults to 24 hours from completion. Once expired, the key can
  execute again with any payload. Expired rows are reused under lock. For storage
  maintenance, periodically delete records with `expires_at <= timezone.now()`;
  choose retention appropriate for clients' retry windows. Response bodies may
  contain private application data and need the same access protection as the
  underlying records.

## Transactions and concurrency

The unique scope/key constraint arbitrates simultaneous first requests. The
service holds a row lock while checking existing records, executing the handler,
and saving the response. Concurrent duplicates wait for the first transaction
and then replay its result. This follows Django's
[transactional row locking](https://docs.djangoproject.com/en/6.0/ref/models/querysets/#select-for-update).
Database lock timeouts may terminate a waiting request; clients can retry it.

Endpoint writes and the response record commit together on the **default
database**. Keep handlers short; this service holds a database transaction while
they execute. A process failure before commit rolls back the record and database
writes, allowing retry. PostgreSQL is the intended production backend; SQLite
does not provide the row-lock guarantees needed for concurrent use.

Transactions cannot roll back external effects (email, S3, payment APIs) or writes
to other databases. Use a transactional outbox or the external provider's own
idempotency support for those operations. `transaction.on_commit` defers an effect
but does not guarantee delivery after a process crash. Do not use this decorator
alone as an exactly-once guarantee for external work.

## Tests

Run the tests against the configured PostgreSQL test database as part of the
normal Django suite:

```text
python manage.py test core.idempotency
```

An isolated local SQLite suite avoids deployment configuration and dotenv files:

```text
python -m django test core.idempotency --settings=core.idempotency.test_settings
```

The concurrency test is skipped on SQLite and runs in the PostgreSQL CI suite.
