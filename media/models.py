from django.db import models
from django.conf import settings

class Image(models.Model):
    image_name = models.CharField(max_length=100)
    resized_image_name = models.CharField(max_length=100, null=True, blank=True)
    thumbnail_name = models.CharField(max_length=100, null=True, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
