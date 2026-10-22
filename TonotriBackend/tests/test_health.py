from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse


class HealthCheckTests(SimpleTestCase):
    def test_liveness_reports_healthy_without_dependency_checks(self):
        response = self.client.get(reverse('health-live'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'healthy'})

    @patch('TonotriBackend.health.redis_is_ready', return_value=True)
    @patch('TonotriBackend.health.database_is_ready', return_value=True)
    def test_readiness_reports_healthy(self, database_check, redis_check):
        response = self.client.get(reverse('health-ready'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'healthy')
        database_check.assert_called_once_with()
        redis_check.assert_called_once_with()

    @patch('TonotriBackend.health.redis_is_ready', return_value=False)
    @patch('TonotriBackend.health.database_is_ready', return_value=True)
    def test_readiness_reports_degraded_when_redis_is_unavailable(
        self,
        database_check,
        redis_check,
    ):
        response = self.client.get(reverse('health-ready'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'degraded')
        self.assertEqual(response.json()['services']['redis'], 'unavailable')

    @patch('TonotriBackend.health.redis_is_ready', return_value=True)
    @patch('TonotriBackend.health.database_is_ready', return_value=False)
    def test_readiness_reports_unhealthy_when_database_is_unavailable(
        self,
        database_check,
        redis_check,
    ):
        response = self.client.get(reverse('health-ready'))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['status'], 'unhealthy')
        self.assertEqual(response.json()['services']['database'], 'unavailable')

    def test_health_checks_only_accept_get_requests(self):
        self.assertEqual(self.client.post(reverse('health-live')).status_code, 405)
        self.assertEqual(self.client.post(reverse('health-ready')).status_code, 405)
