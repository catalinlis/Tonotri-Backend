from rest_framework import serializers
from .models import User
from media.serializers import ImageSerializer
from django.conf import settings


class ProfilePhotoUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)

    def validate_file(self, value):
        max_size = 5 * 1024 * 1024
        allowed_types = {"image/jpeg", "image/png", "image/webp"}

        if value.size > max_size:
            raise serializers.ValidationError("Image must be 5 MB or smaller.")

        content_type = getattr(value, "content_type", None)
        if content_type not in allowed_types:
            raise serializers.ValidationError("Upload a JPEG, PNG, or WebP image.")

        return value

class VisitedCountriesSerializer(serializers.Serializer):
    codes = serializers.ListField(
        child=serializers.CharField(min_length=2, max_length=2),
        allow_empty=False,
    )

    def validate_codes(self, value):
        return list(dict.fromkeys(code.strip().upper() for code in value))

class UserSerializer(serializers.ModelSerializer):
    image_path = serializers.SerializerMethodField()
    visited_countries = serializers.SlugRelatedField(many=True, read_only=True, slug_field="country_name")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'birthday', 'gender', 'image_path', 'visited_countries']
        
    def get_image_path(self, obj):
        if obj.profile_image == None:
            return None

        if obj.profile_image.thumbnail_name:
            return f"https://{settings.AWS_CLOUDFRONT_DISTRIBUTION}/{obj.profile_image.thumbnail_name}"

        return  f"https://{settings.AWS_CLOUDFRONT_DISTRIBUTION}/{obj.profile_image.image_name}"

class UserPersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'birthday', 'gender']
