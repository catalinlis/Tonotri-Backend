from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services import S3Service
from .models import Image

class ImageViewSet(ModelViewSet):
    queryset = Image.objects.all()
    permission_classes = [IsAuthenticated]

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
            status=status.HTTP_201_OK
        )
