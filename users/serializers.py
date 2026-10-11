from rest_framework import serializers
from .models import User
from media.serializers import ImageSerializer
from django.conf import settings

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