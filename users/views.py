from django.conf import settings
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    ProfilePhotoUploadSerializer,
    UserPersonalInfoSerializer,
    UserSerializer,
    VisitedCountriesSerializer,
)
from media.services import S3Service
from media.models import Image
from media.serializers import ImageSerializer
from .models import User
from explore.models import Country

from core.idempotency.decorators import idempotent
from core.idempotency.fingerprint import digest, file_fingerprint
from core.outbox.models import OutboxEvent

import logging
from uuid import UUID

logger = logging.getLogger(__name__)

PROFILE_PHOTO_RAW_BUCKET_PATH = 'images/profile-photo/raw/'
PROFILE_PHOTO_RESIZED_BUCKET_PATH = 'images/profile-photo/resized'

class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Never expose another user's account through generic CRUD routes."""
        return User.objects.filter(pk=self.request.user.pk)

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='me/personal-info')
    def personal_info(self, request):
        serializer = UserPersonalInfoSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put'], url_path='me/profile-photo')
    @idempotent(scope='upload_profile_photo')
    def upload_profile_photo(self, request):
        user = request.user
        input_serializer = ProfilePhotoUploadSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        file = input_serializer.validated_data['file']
        
        try:
            s3_service = S3Service()

            # Hash the components together to stay within Image.image_name's
            # 100-character limit while isolating users, operations and content.
            operation_id = str(UUID(request.headers['Idempotency-Key']))
            filename = digest([str(user.pk), operation_id, file_fingerprint(file)])
            extension = {
                'image/jpeg': 'jpg',
                'image/png': 'png',
                'image/webp': 'webp',
            }[file.content_type]
            object_key = f'{PROFILE_PHOTO_RAW_BUCKET_PATH}{filename}.{extension}'

            key = s3_service.upload_file(
                file=file, 
                user_id=user.id, 
                prefix=PROFILE_PHOTO_RAW_BUCKET_PATH,
                key=object_key,
            )

            image = Image.objects.create(
                image_name=key,
                uploaded_by=user
            )

            user.profile_image = image
            user.save()

            OutboxEvent.objects.create(
                event_type='image.process',
                payload={
                    'event': 'image.process',
                    'image_id': str(image.id),
                    's3_key': key,
                    'bucket_name': settings.AWS_BUCKET_NAME,
                },
            )

            return Response({
                    'message': 'Profile photo updated',
                    'profile_image': ImageSerializer(image, context={'request': request}).data
                }, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception("Profile photo upload failed")
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(detail=False, methods=['put'], url_path='me/countries')
    def add_countries(self, request):
        input_serializer = VisitedCountriesSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        codes = input_serializer.validated_data['codes']

        countries = Country.objects.filter(alpha2__in=codes)

        if countries.count() == 0:
            return Response(
                {'status': 'No countries found.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.visited_countries.set(countries)

        return Response(
            {'status': 'Visited countries added.'},
            status=status.HTTP_200_OK
        )
