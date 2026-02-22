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
            contents = res.get("Contents", [])
            
            return [
                {
                    "Key": str(obj["Key"]),
                    "Size": obj["Size"],
                    "LastModified": obj["LastModified"].isoformat() if "LastModified" in obj else None,
                    "ETag": str(obj["ETag"]),
                    "StorageClass": obj.get("StorageClass", "STANDARD")
                }
                for obj in contents
            ]
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
            
            # Check if local_path is a directory (ends with slash or is existing directory)
            if local_path.endswith("/") or os.path.isdir(local_path):
                # If it's a directory, create the full file path
                filename = os.path.basename(key)
                local_file_path = os.path.join(local_path, filename)
            else:
                # Assume it's already a full file path
                local_file_path = local_path
            
            # Ensure the directory exists (THIS LINE SHOULD STAY)
            directory = os.path.dirname(local_file_path)
            os.makedirs(directory, exist_ok=True, mode=0o755) 
            
            # Download the file (THIS LINE SHOULD STAY)
            with open(local_file_path, "wb") as file:
                self.connection.download_fileobj(settings.AWS_STORAGE_BUCKET_NAME, key, file)
            
            return local_file_path
        except ClientError as error:
            logger.error(f"Error downloading file {key}: {error}")
            return None
    
    
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