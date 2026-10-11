from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class UserAuthorizationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="traveler_one",
            email="one@example.com",
            password="StrongPass1",
            birthday=date(1990, 1, 1),
            regular_user=True,
            confirmed_email=True,
        )
        self.other_user = User.objects.create_user(
            username="traveler_two",
            email="two@example.com",
            password="StrongPass1",
            birthday=date(1991, 1, 1),
            regular_user=True,
            confirmed_email=True,
        )

    def test_anonymous_user_cannot_access_current_user(self):
        response = self.client.get(reverse("users-me"))

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_authenticated_user_can_access_current_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("users-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)

    def test_user_list_contains_only_the_authenticated_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("users-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], self.user.username)

    def test_user_cannot_retrieve_another_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(
            reverse("users-detail", kwargs={"pk": self.other_user.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_another_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            reverse("users-detail", kwargs={"pk": self.other_user.pk}),
            {"first_name": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.other_user.refresh_from_db()
        self.assertNotEqual(self.other_user.first_name, "Changed")

    def test_user_cannot_delete_another_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(
            reverse("users-detail", kwargs={"pk": self.other_user.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(User.objects.filter(pk=self.other_user.pk).exists())
