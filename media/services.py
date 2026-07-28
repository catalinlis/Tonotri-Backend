from django.conf import settings
import boto3
import uuid

s3 = boto3.client('s3')

BUCKET_NAME = 'tonotri-application'
PROFILE_PHOTO_RAW_PREFIX = 'profile-photo/raw/'
PROFILE_PHOTO_RESIZED_PREFIX = 'profile-photo/resized/'

class S3Service:
    def __init__(self):
        self.bucket_name = BUCKET_NAME
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

    def upload_file(self, file, user_id, prefix):
        extension = file.name.split('.')[-1]
        filename = f'{user_id}_{uuid.uuid4()}.{extension}'
        key = f'{prefix}{filename}'

        self.s3.upload_fileobj(file, self.bucket_name, key)

        return key
