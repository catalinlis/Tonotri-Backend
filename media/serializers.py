from rest_framework import serializers
from .models import Image

class ImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Image
        fields = [
            'id',
            'image_name',
            'resized_image_name',
            'thumbnail_name',
            'uploaded_by',
            'created_at',
        ]
        read_only_fields = fields

class ImageUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)

    def validate_file(self, value):
        max_size = 10 * 1024 * 1024
        allowed_types = {'image/jpeg', 'image/png', 'image/webp'}

        if value.size > max_size:
            raise serializers.ValidationError('Image must be 10MB or smaller.')

        content_type = getattr(value, 'content_type', None)
        if content_type not in allowed_types:
            raise serializers.ValidationError('Upload a JPEG, PNG, or WebP image.')

        return value
