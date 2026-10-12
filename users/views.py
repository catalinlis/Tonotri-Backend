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
from media.services import S3Service, SQSService
from media.models import Image
from media.serializers import ImageSerializer
from .models import User
from explore.models import Country

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
    def upload_profile_photo(self, request):
        user = request.user
        input_serializer = ProfilePhotoUploadSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        file = input_serializer.validated_data['file']
        
        try:
            s3_service = S3Service()

            key = s3_service.upload_file(
                file=file, 
                user_id=user.id, 
                prefix=PROFILE_PHOTO_RAW_BUCKET_PATH
            )

            image = Image.objects.create(
                image_name=key,
                uploaded_by=user
            )

            user.profile_image = image
            user.save()

            sqs_service = SQSService()
            sqs_service.send_image_processing_message(image.id, key)

            return Response({
                    'message': 'Profile photo updated',
                    'profile_image': ImageSerializer(image, context={'request': request}).data
                }, status=status.HTTP_200_OK
            )

        except Exception as e:
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
