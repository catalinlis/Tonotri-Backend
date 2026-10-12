from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from users.models import User

from .models import Image
from .serializers import ImageUploadSerializer


class ImageUploadSerializerTests(APITestCase):
    def test_accepts_supported_image_content_type(self):
        upload = SimpleUploadedFile(
            "photo.jpg",
            b"test-image-content",
            content_type="image/jpeg",
        )
        serializer = ImageUploadSerializer(data={"file": upload})

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_unsupported_content_type(self):
        upload = SimpleUploadedFile(
            "notes.txt",
            b"not-an-image",
            content_type="text/plain",
        )
        serializer = ImageUploadSerializer(data={"file": upload})

        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)


class ImageAuthorizationTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="image_owner",
            email="owner@example.com",
            password="StrongPass1",
            birthday=date(1990, 1, 1),
        )
        self.other_user = User.objects.create_user(
            username="image_viewer",
            email="viewer@example.com",
            password="StrongPass1",
            birthday=date(1990, 1, 1),
        )
        self.owner_image = Image.objects.create(
            image_name="images/owner/photo.jpg",
            uploaded_by=self.owner,
        )
        self.other_image = Image.objects.create(
            image_name="images/viewer/photo.jpg",
            uploaded_by=self.other_user,
        )

    def test_anonymous_user_cannot_list_images(self):
        response = self.client.get(reverse("images-list"))

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_image_list_is_scoped_to_authenticated_owner(self):
        self.client.force_authenticate(self.owner)

        response = self.client.get(reverse("images-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item["id"] for item in response.data}
        self.assertEqual(returned_ids, {self.owner_image.id})

    def test_user_cannot_retrieve_another_users_image(self):
        self.client.force_authenticate(self.owner)

        response = self.client.get(
            reverse("images-detail", kwargs={"pk": self.other_image.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_another_users_image(self):
        self.client.force_authenticate(self.owner)

        response = self.client.patch(
            reverse("images-detail", kwargs={"pk": self.other_image.pk}),
            {"thumbnail_name": "tampered.jpg"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.other_image.refresh_from_db()
        self.assertIsNone(self.other_image.thumbnail_name)

    def test_user_cannot_delete_another_users_image(self):
        self.client.force_authenticate(self.owner)

        response = self.client.delete(
            reverse("images-detail", kwargs={"pk": self.other_image.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Image.objects.filter(pk=self.other_image.pk).exists())
