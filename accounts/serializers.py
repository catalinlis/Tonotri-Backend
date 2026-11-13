from rest_framework import serializers
from auth_kit.serializers import RegisterSerializer
from auth_kit.serializers.login_factors import LoginRequestSerializer as AuthKitLoginRequestSerializer
from rest_framework.exceptions import PermissionDenied
from allauth.account.adapter import get_adapter
from auth_kit.social.serializers.login import get_social_login_serializer
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()


def get_custom_social_login_serializer(provider_name=''):
    base_serializer = get_social_login_serializer(provider_name)

    class SocialLoginSerializer(base_serializer):
        def handle_social_login(self, request, login):
            # Capture provider-verified addresses before account linking changes
            # login.user or synchronizes local email records.
            verified_emails = {
                address.email.casefold()
                for address in login.email_addresses
                if address.verified and address.email
            }
            trusted_provider = login.account.provider == 'google'
            super().handle_social_login(request, login)

            user = login.user
            if (
                trusted_provider
                and not user.confirmed_email
                and user.email.casefold() in verified_emails
            ):
                user.confirmed_email = True
                user.save(update_fields=['confirmed_email'])

        def set_login_user(self, login):
            # Auth Kit defaults to the full email, which can exceed username's
            # max_length. Allauth generates a bounded, unique username instead.
            if not login.user.pk:
                if login.account and login.account.provider == 'google':
                    for field in ('first_name', 'last_name'):
                        value = getattr(login.user, field)
                        if value:
                            max_length = User._meta.get_field(field).max_length
                            setattr(login.user, field, value.title()[:max_length])
                login.user.username = get_adapter(self.context.get('request')).generate_unique_username([
                    login.user.username,
                    login.user.email,
                    'user',
                ])

    return SocialLoginSerializer


class LoginRequestSerializer(AuthKitLoginRequestSerializer):
    username = serializers.CharField(max_length=20, trim_whitespace=True, write_only=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def get_auth_user(self, username, email, password):
        user = super().get_auth_user(username, email, password)
        if user is None:
            raise PermissionDenied({'error': 'Wrong password or account.'})
        return user

    def validate_email_verification_status(self, user):
        super().validate_email_verification_status(user)
        if user.regular_user and not user.confirmed_email:
            raise PermissionDenied({
                'error': 'Email is not confirmed.',
                'guid': str(user.guid),
            })

class GuidRequestSerializer(serializers.Serializer):
    guid = serializers.UUIDField()

class VerificationCodeSerializer(GuidRequestSerializer):
    code = serializers.RegexField(
        regex=r'^\d{6}$',
        write_only=True,
        error_messages={'invalid': 'Code must contain exactly 6 digits.'},
    )

class CustomRegisterSerializer(RegisterSerializer):
    username_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9]+([._-]?[a-zA-Z0-9]+)*$',
        message="Username can contain letters, numbers, and . _ - (not consecutive)."
    )

    name_validator = RegexValidator(
        regex=r'^[A-Za-z]+(-[A-Za-z]+)?$',
        message="Name must contain only letters and at most one hyphen."
    )

    password_validator = RegexValidator(
        regex=r'^(?=.*[A-Z])(?=.*[0-9]).*$',
        message="Password must contain at least one uppercase letter and one number."
    )

    username = serializers.CharField(
        required=True,
        min_length=6,
        max_length=20,
        validators=[username_validator]
    )

    email = serializers.EmailField(required=True)

    first_name = serializers.CharField(
        required=True,
        min_length=2,
        max_length=20,
        validators=[name_validator]
    )

    last_name = serializers.CharField(
        required=True,
        min_length=2,
        max_length=20,
        validators=[name_validator]
    )

    birthday = serializers.DateField(required=True)

    gender = serializers.ChoiceField(
        choices=User.Gender.choices,
        required=True
    )

    password1 = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[password_validator]
    )

    password2 = serializers.CharField(
        write_only=True,
        min_length=8
    )

    # -------------------------
    # Field validations
    # -------------------------

    def validate_email(self, value):
        email = value.lower().strip()

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return email

    def validate_username(self, value):
        username = value.lower().strip()

        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return username

    def validate_birthday(self, value):
        today = date.today()

        if value >= today:
            raise serializers.ValidationError(
                "Birthday must be in the past."
            )

        age = (
            today.year
            - value.year
            - ((today.month, today.day) < (value.month, value.day))
        )

        if age < 18:
            raise serializers.ValidationError(
                "You must be at least 18 years old."
            )

        return value

    def validate(self, attrs):
        if attrs["password1"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password2": "Passwords do not match."}
            )
        return attrs

    # -------------------------
    # Create user
    # -------------------------

    def save(self):
        # super().save(request) handles the initial user creation 
        # and allauth's email confirmation logic.
        user = super().save()
    
        # Update the additional custom fields
        user.first_name = self.validated_data.get("first_name")
        user.last_name = self.validated_data.get("last_name")
        user.birthday = self.validated_data.get("birthday")
        user.gender = self.validated_data.get("gender")
        user.regular_user = True
    
        user.save()
        
        return user

class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Returned on login, registration, and GET /api/auth/user/
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ['id', 'email']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
