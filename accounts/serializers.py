from rest_framework import serializers
from auth_kit.serializers import RegisterSerializer
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()

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