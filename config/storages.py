from storages.backends.s3boto3 import S3Boto3Storage
from botocore.exceptions import ClientError
from django.conf import settings
import boto3
import os
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#======================================= ArvanCloudStorage ====================================

class ArvanCloudStorage(S3Boto3Storage):
    location = "media"  


#======================================= Bucket ================================================

class Bucket:
    def __init__(self):
        session = boto3.session.Session()
        self.connection = session.client(
            service_name="s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, 
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            region_name=settings.AWS_S3_REGION_NAME,
        )
    
    def get_files(self):
        try:
            res = self.connection.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            return res.get("Contents", [])
        except ClientError as error:
            logger.error(f"Error listing files: {error}")
            return []
    
    
    def delete_file(self, key):
        try:
            return self.connection.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
        except ClientError as error:
            logger.error(f"Error deleting file {key}: {error}")
            return None
    
    
    def download_file(self, key, local_path=None):
        try:
            if not local_path:
                local_path = os.path.join(settings.AWS_LOCAL_STORAGE, key)
                
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, "wb") as file:
                self.connection.download_fileobj(settings.AWS_STORAGE_BUCKET_NAME, key, file)
            return local_path
        except ClientError as error:
            logger.error(f"Error downloading file {key}: {error}")
            return None
    
    
    def file_exists(self, key):
        try:
            self.connection.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
            return True
        except ClientError:
            return False
    
    
    def get_file_url(self, key, expires=3600):
        try:
            return self.connection.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
                ExpiresIn=expires
            )
        except ClientError as error:
            logger.error(f"Error generating URL for {key}: {error}")
            return None

    
#===============================================================================================

# bucket = Bucket()


# if bucket.file_exists("some-file.txt"):
#     bucket.download_file("some-file.txt")
    
# # Generate temporary access URL
# temp_url = bucket.get_file_url("file.jpg", expires=300)  # 5 min access