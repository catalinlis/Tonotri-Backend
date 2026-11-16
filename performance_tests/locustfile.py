"""HTTP load test for concurrent requests to the same AI description key."""

import os
import sys
from getpass import getpass

from gevent.event import Event
from locust import HttpUser, constant, events, task


ready = Event()


@events.init_command_line_parser.add_listener
def options(parser):
    parser.add_argument('--test-country', default='Germany',
                        help='Existing country requested by every simulated user')


@events.init.add_listener
def authentication(environment, **kwargs):
    # No credentials in command-line arguments, source files, or log output.
    cookie = os.environ.get('LOCUST_AUTH_COOKIE', '').strip()
    if not cookie and sys.stdin.isatty():
        cookie = getpass('Test account auth-jwt cookie (hidden): ').strip()
    if not cookie:
        raise SystemExit('Supply LOCUST_AUTH_COOKIE or run in a terminal for hidden input.')
    environment.test_auth_cookie = cookie


@events.test_start.add_listener
def reset_burst(**kwargs):
    ready.clear()


@events.spawning_complete.add_listener
def release_burst(**kwargs):
    # Network/server scheduling still determines arrival times at the backend.
    ready.set()


class CountryDescriptionUser(HttpUser):
    wait_time = constant(1)

    def on_start(self):
        # Explicit header also works with localhost cookie-domain handling.
        # Requests below never follow redirects to another destination.
        self.client.headers['Cookie'] = f'auth-jwt={self.environment.test_auth_cookie}'

    @task
    def description(self):
        ready.wait()
        with self.client.get(
            '/api/explore/country-description/',
            params={'country': self.environment.parsed_options.test_country},
            name='Country description (same cache key)',
            timeout=60,
            allow_redirects=False,
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f'Expected HTTP 200, got {response.status_code}')
                return
            try:
                payload = response.json()
            except ValueError:
                response.failure('Response is not JSON')
                return
            if not isinstance(payload, dict) or not payload or 'error' in payload:
                response.failure('Expected a nonempty description object')
