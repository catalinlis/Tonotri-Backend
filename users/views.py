from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer, UserPersonalInfoSerializer
from media.services import S3Service
from media.models import Image
from media.serializers import ImageSerializer
from .models import User
from explore.models import Country

PROFILE_PHOTO_RAW_BUCKET_PATH = 'images/profile-photo/raw/'
PROFILE_PHOTO_RESIZED_BUCKET_PATH = 'images/profile-photo/resized'

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

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
        file = request.FILES.get('file')

        if not file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

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

        return Response({
                'message': 'Profile photo updated',
                'profile_image': ImageSerializer(image, context={'request': request}).data
            }, status=status.HTTP_200_OK
        )
        
    @action(detail=False, methods=['put'], url_path='me/countries')
    def add_countries(self, request):
        codes = request.data.get('codes', [])

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