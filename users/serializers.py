from rest_framework import serializers
from .models import User
from media.serializers import ImageSerializer

class UserSerializer(serializers.ModelSerializer):
    profile_image = ImageSerializer(read_only=True)

    class Meta:
        model = User
        fields = '__all__'
        read_only_fields = ['id', 'profile_image']

class UserPersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'birthday', 'gender']