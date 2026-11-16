# Cache stampede performance test (Locust)

This test sends real HTTP requests to `/api/explore/country-description/`.
All users request the same country and compete for the same cache key. Initial
requests wait until all Locust users have spawned. Thereafter each user waits
one second after a response before requesting again.

## Setup

Run from the repository root, next to `manage.py`:

```powershell
py -m pip install -r performance_tests/requirements.txt
```

Start the backend and its Redis/database using your normal local or staging
setup. The test uses the running application's configuration. It does not start
Redis, load Django, read dotenv files, or mock the AI provider. Cache misses can
therefore make paid AI calls. For repeatable timings, configure a fixed-delay AI
stub on the test backend separately.

Log in with an active, email-confirmed test account. In browser developer tools,
copy just the value of the `auth-jwt` cookie. The startup prompt accepts it as
hidden input; do not paste it into source files or commands. For automated runs,
inject `LOCUST_AUTH_COOKIE` through your secret manager. Use a fresh cookie if
authentication expires during a run.

Romania must exist in the database. Use `--test-country France` to select another
existing country.

## Interactive test

```powershell
locust -f performance_tests/locustfile.py --host http://localhost:8000
```

Enter the cookie in the terminal, then open http://localhost:8089. Start with
100 users and a spawn rate of 100 users/second. HTTP 503, authentication failures,
redirects and invalid JSON are failures, not successful fast responses.

## Exercise cache expiration

A warm cache alone does not test stampede protection:

1. Run a cold-cache test with the tested entry absent in an isolated test cache.
2. Run again while the entry is warm to measure the cache-hit baseline.
3. On the test backend, configure a short `AI_DESCRIPTION_CACHE_TTL` such as
   15 seconds, restart it, and ensure the tested entry was created with that
   TTL. Existing entries retain their old TTL. Run long enough for several
   expirations. Do not flush a shared application Redis instance.
4. Compare expiration intervals separately from warm-cache traffic. Keep the
   same AI delay, worker count, TTL and load settings on both branches.

The backend currently defaults to a 24-hour cache TTL and a five-second follower
wait. Slow generation may produce 503 responses, retain those in the report.

