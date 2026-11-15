# AI description coordination

Country, city, landmark descriptions and landmark variations share Redis cache
and lock handling in `BaseDescriptionAI`. All workers must use the same Redis
database. Cache keys include normalized parameters, model, schema and
`AI_DESCRIPTION_PROMPT_VERSION`. Increment that version when prompts change.

On a cache miss, only the owner of the request's Redis lock can generate.
The owner checks the cache again after acquiring the lock. Other requests poll
with jitter for up to `AI_DESCRIPTION_LOCK_WAIT`.
The 30-second `AI_DESCRIPTION_LOCK_TTL` is renewed every 10 seconds while the
owner works. Redis operations have two-second connection and socket timeouts;
these can add to the polling deadline. Release verifies the ownership token.

Redis failures, lost ownership and waiting timeouts produce HTTP 503 with
`Retry-After: 5` and the code `AI_SERVICE_TEMPORARILY_UNAVAILABLE`. Clients should
use bounded retries with backoff and jitter. Generation never deliberately
bypasses Redis coordination. The standard Django REST Framework exception
handler supplies the response and Retry-After header.

The result is cached before usage accounting. Database accounting failures are
logged, they do not discard a cached success or hide a coordination error.
Failed usage writes are not automatically retried.

This prevents ordinary concurrent cache misses from generating duplicate work,
not exactly-once billing across failures. A crash after the provider completes,
Redis data loss, or lease loss during an in-flight provider request can still
cause duplicate work. Losing a lease does not cancel an already submitted call.
Deploy updated workers together: older workers do not participate in locking.
