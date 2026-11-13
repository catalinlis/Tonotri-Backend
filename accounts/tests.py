from datetime import date
from unittest.mock import patch
from django.contrib.auth import authenticate

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from .serializers import LoginRequestSerializer, VerificationCodeSerializer


class SocialUsernameTests(APITestCase):
    def test_google_signup_capitalizes_names(self):
        from allauth.socialaccount.models import SocialAccount, SocialLogin
        from .views import GoogleLogin

        user = User(email='names@example.com', first_name='jOHN', last_name='van dyke')
        login = SocialLogin(user=user, account=SocialAccount(provider='google', uid='names'))
        serializer = GoogleLogin().get_serializer_class()(context={'request': None})
        serializer.set_login_user(login)
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Van Dyke')

    def prepare_user(self, email, username=''):
        from allauth.socialaccount.models import SocialAccount, SocialLogin
        from .views import GoogleLogin

        user = User(email=email, username=username)
        serializer = GoogleLogin().get_serializer_class()(context={'request': None})
        serializer.set_login_user(SocialLogin(
            user=user, account=SocialAccount(provider='google', uid=email),
        ))
        return user

    def test_long_email_generates_bounded_username(self):
        user = self.prepare_user('a-very-long-google-account-name@example.com')
        self.assertTrue(user.username)
        self.assertLessEqual(len(user.username), User._meta.get_field('username').max_length)
        user.save()
        user.refresh_from_db()
        self.assertIsNone(user.birthday)

    def test_generated_usernames_remain_unique(self):
        first = self.prepare_user('a-very-long-google-account-name@example.com')
        first.save()
        second = self.prepare_user('a-very-long-google-account-name@another.example')
        self.assertNotEqual(first.username, second.username)
        self.assertLessEqual(len(second.username), 20)
        second.save()

    def test_existing_username_is_preserved(self):
        from allauth.socialaccount.models import SocialLogin
        from .views import GoogleLogin

        user = User.objects.create_user(
            username='existing_user', email='existing@example.com',
            first_name='eXisting', last_name='de Silva',
        )
        serializer = GoogleLogin().get_serializer_class()(context={'request': None})
        serializer.set_login_user(SocialLogin(user=user))
        self.assertEqual(user.username, 'existing_user')
        self.assertEqual(user.first_name, 'eXisting')
        self.assertEqual(user.last_name, 'de Silva')


class SocialEmailConfirmationTests(APITestCase):
    def setUp(self):
        from .views import GoogleLogin

        self.user = User.objects.create_user(
            username='regular_user', email='owner@example.com',
            password='StrongPass1', regular_user=True, confirmed_email=False,
        )
        self.serializer = GoogleLogin().get_serializer_class()(context={'request': None})

    def social_login(self, email='owner@example.com', verified=True, provider='google'):
        from allauth.account.models import EmailAddress
        from allauth.socialaccount.models import SocialAccount, SocialLogin

        return SocialLogin(
            user=self.user,
            account=SocialAccount(provider=provider, uid='provider-user'),
            email_addresses=[EmailAddress(email=email, verified=verified)],
        )

    @patch('auth_kit.social.serializers.login.SocialLoginWithTokenRequestSerializer.handle_social_login')
    def test_verified_google_email_confirms_regular_account(self, handle_login):
        self.serializer.handle_social_login(None, self.social_login(email='OWNER@example.com'))
        handle_login.assert_called_once()
        self.user.refresh_from_db()
        self.assertTrue(self.user.confirmed_email)
        self.assertTrue(self.user.regular_user)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(reverse('profile')).status_code, 200)

    @patch('auth_kit.social.serializers.login.SocialLoginWithTokenRequestSerializer.handle_social_login')
    def test_untrusted_or_nonmatching_email_does_not_confirm(self, handle_login):
        for kwargs in (
            {'verified': False},
            {'email': 'another@example.com'},
            {'provider': 'untrusted'},
        ):
            with self.subTest(**kwargs):
                self.serializer.handle_social_login(None, self.social_login(**kwargs))
                self.user.refresh_from_db()
                self.assertFalse(self.user.confirmed_email)

    @patch(
        'auth_kit.social.serializers.login.SocialLoginWithTokenRequestSerializer.handle_social_login',
        side_effect=ValueError('Login failed'),
    )
    def test_failed_login_does_not_confirm_email(self, handle_login):
        with self.assertRaises(ValueError):
            self.serializer.handle_social_login(None, self.social_login())
        self.user.refresh_from_db()
        self.assertFalse(self.user.confirmed_email)


class AccountSerializerTests(APITestCase):
    def test_login_serializer_trims_username_but_not_password(self):
        serializer = LoginRequestSerializer(
            data={"username": "  traveler  ", "password": " password "}
        )

        self.assertEqual(serializer.fields['username'].run_validation('  traveler  '), 'traveler')
        self.assertEqual(serializer.fields['password'].run_validation(' password '), ' password ')

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
    @patch("auth_kit.serializers.login_factors.authenticate", return_value=None)
    def test_login_rejects_invalid_credentials(self, authenticate_mock):
        response = self.client.post(
            reverse("login"),
            {"username": "missing_user", "password": "wrong"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        authenticate_mock.assert_called_once()

    @patch("auth_kit.serializers.login_factors.authenticate")
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
        self.assertNotIn('auth-jwt', response.cookies)
        authenticate_mock.assert_called_once()

    def test_successful_login_authenticates_once_and_sets_cookies(self):
        user = User.objects.create_user(
            username='login_user', email='login@example.com',
            password=' StrongPass1 ', regular_user=True, confirmed_email=True,
        )
        with patch('auth_kit.serializers.login_factors.authenticate', wraps=authenticate) as auth_mock:
            response = self.client.post(reverse('login'), {
                'username': '  login_user  ', 'password': ' StrongPass1 ',
            }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        auth_mock.assert_called_once()
        self.assertEqual(response.data['user']['pk'], user.pk)
        self.assertTrue(response.cookies['auth-jwt']['httponly'])
        self.assertTrue(response.cookies['auth-refresh-jwt']['httponly'])
        self.assertEqual(response.cookies['loggedIn'].value, 'true')

    def test_inactive_user_cannot_login(self):
        User.objects.create_user(
            username='inactive_user', email='inactive@example.com',
            password='StrongPass1', regular_user=True, confirmed_email=True,
            is_active=False,
        )
        response = self.client.post(reverse('login'), {
            'username': 'inactive_user', 'password': 'StrongPass1',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('auth-jwt', response.cookies)


class ProtectedEndpointConfirmationTests(APITestCase):
    create_user = ActiveUserAuthorizationTests.create_user

    def test_unconfirmed_user_cannot_access_users_or_media(self):
        self.client.force_authenticate(self.create_user(confirmed_email=False))
        for route in ('users-me', 'users-list', 'images-list'):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(reverse(route)).status_code, 403)


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
