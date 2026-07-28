from rest_framework import serializers
from .models import Image

class ImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Image
        fields = '__all__'
        read_only_fields = ['id', 'image_name', 'uploaded_by', 'created_at']