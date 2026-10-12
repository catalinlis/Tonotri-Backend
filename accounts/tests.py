from datetime import date
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from .serializers import LoginRequestSerializer, VerificationCodeSerializer


class AccountSerializerTests(APITestCase):
    def test_login_serializer_trims_username_but_not_password(self):
        serializer = LoginRequestSerializer(
            data={"username": "  traveler  ", "password": " password "}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["username"], "traveler")
        self.assertEqual(serializer.validated_data["password"], " password ")

    def test_verification_code_accepts_exactly_six_digits(self):
        serializer = VerificationCodeSerializer(
            data={"guid": "9f601abe-52e4-4d89-a658-39bb3595599e", "code": "123456"}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_verification_code_rejects_non_digits(self):
        serializer = VerificationCodeSerializer(
            data={"guid": "9f601abe-52e4-4d89-a658-39bb3595599e", "code": "abcdef"}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("code", serializer.errors)


class ActiveUserAuthorizationTests(APITestCase):
    def create_user(self, **overrides):
        values = {
            "username": "active_user",
            "email": "active@example.com",
            "password": "StrongPass1",
            "birthday": date(1990, 1, 1),
            "is_active": True,
            "regular_user": True,
            "confirmed_email": True,
        }
        values.update(overrides)
        return User.objects.create_user(**values)

    def test_profile_rejects_anonymous_user(self):
        response = self.client.get(reverse("profile"))

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_profile_rejects_inactive_user(self):
        user = self.create_user(is_active=False)
        self.client.force_authenticate(user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_profile_rejects_unconfirmed_regular_user(self):
        user = self.create_user(confirmed_email=False)
        self.client.force_authenticate(user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_profile_allows_confirmed_regular_user(self):
        user = self.create_user()
        self.client.force_authenticate(user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], user.email)

    def test_profile_allows_active_social_user_without_custom_confirmation(self):
        user = self.create_user(regular_user=False, confirmed_email=False)
        self.client.force_authenticate(user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LoginAuthenticationTests(APITestCase):
    @patch("accounts.views.authenticate", return_value=None)
    def test_login_rejects_invalid_credentials(self, authenticate_mock):
        response = self.client.post(
            reverse("login"),
            {"username": "missing_user", "password": "wrong"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        authenticate_mock.assert_called_once()

    @patch("accounts.views.authenticate")
    def test_login_rejects_unconfirmed_regular_user(self, authenticate_mock):
        user = User(
            username="unconfirmed_user",
            email="unconfirmed@example.com",
            regular_user=True,
            confirmed_email=False,
        )
        authenticate_mock.return_value = user

        response = self.client.post(
            reverse("login"),
            {"username": user.username, "password": "StrongPass1"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["guid"], str(user.guid))


class EmailVerificationAuthorizationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="verify_user",
            email="verify@example.com",
            password="StrongPass1",
            birthday=date(1990, 1, 1),
            regular_user=True,
            confirmed_email=False,
        )

    @patch("accounts.views.VerificationEmail.compare_code", return_value=True)
    def test_valid_code_confirms_user(self, compare_code_mock):
        response = self.client.post(
            reverse("validate_token"),
            {"guid": str(self.user.guid), "code": "123456"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.confirmed_email)
        compare_code_mock.assert_called_once_with(self.user.email, "123456")

    @patch("accounts.views.VerificationEmail.compare_code", return_value=False)
    def test_invalid_code_does_not_confirm_user(self, compare_code_mock):
        response = self.client.post(
            reverse("validate_token"),
            {"guid": str(self.user.guid), "code": "000000"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.confirmed_email)
        compare_code_mock.assert_called_once_with(self.user.email, "000000")
