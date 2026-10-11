from django.conf import settings
import boto3
import uuid
import json

s3 = boto3.client('s3')

PROFILE_PHOTO_RAW_PREFIX = 'images/profile-photo/raw'
PROFILE_PHOTO_RESIZED_PREFIX = 'images/profile-photo/resized'

class S3Service:
    def __init__(self):
        self.bucket_name = settings.AWS_BUCKET_NAME
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

    def exists_resized_photo(self, file):
        try:
            file_path = f'{PROFILE_PHOTO_RESIZED_PREFIX}/{file}'
            print(file_path)
            self.s3.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )

            return file_path
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            # Else raise the error
            raise

    def generate_presigned_url(self, file_path, expiration=3600):
        try:
            return self.s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": file_path,
                },
                ExpiresIn=expiration,
            )
        except botocore.exceptions.ClientError as e:
            print(f"Error generating presigned URL: {e}")
            raise

class CloudFrontService:

    @staticmethod
    def get_image_url(key: str) -> str | None:
        if not key:
            return None
        
        return f'https://{settings.AWS_CLOUDFRONT_DISTRIBUTION}/{key}'

class SQSService:

    def __init__(self):
        self.client = boto3.client(
            'sqs',
            region_name = settings.AWS_REGION
        )

    def send_image_processing_message(self, image_id, s3_key):

        message = {
            'event': 'image.process',
            'image_id': str(image_id),
            's3_key': s3_key,
            'bucket_name': settings.AWS_BUCKET_NAME
        }

        self.client.send_message(
            QueueUrl=settings.AWS_SQS_IMAGE_PROCESSING_URL,
            MessageBody=json.dumps(message)
        )