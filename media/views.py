from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services import S3Service, CloudFrontService
from .models import Image
from .serializers import ImageSerializer
import time

class ImageViewSet(ModelViewSet):
    queryset = Image.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ImageSerializer

    def get_queryset(self):
        return Image.objects.filter(uploaded_by=self.request.user)

    def create(self, request, *args, **kwargs):
        file = request.FILES.get("file")

        if not file:
            return Response(
                {'error': 'No file provided'},
                status = status.HTTP_400_BAD_REQUEST
            )

        s3_service = S3Service()
        key = s3_service.upload_file(file, request.user.id)

        image = Image.objects.create(
            image_name = key,
            uploaded_by = request.user
        )

        return Response({
                'id': image.id,
                'key': image.image_name
            },
            status=status.HTTP_201_CREATED
        )

    def retrieve(self, request, *args, **kwargs):
        start = time.perf_counter()
        image = self.get_object()
        image_uid = image.image_name.split('/')[-1]

        s3_service = S3Service()

        if photo_path:=s3_service.exists_resized_photo(image_uid):
            pass
        else:
            photo_path = image.image_name

        url = CloudFrontService.get_image_url(photo_path)

        if not url:
            return Response({'error': 'Could not get image URL'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            { 'url': url },
            status=status.HTTP_200_OK
        )
