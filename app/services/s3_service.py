import boto3
import uuid
from fastapi import UploadFile
from botocore.exceptions import ClientError
from typing import Optional
import os
from datetime import datetime

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.base_url = f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION', 'us-east-1')}.amazonaws.com"
    
    # -------------------------------------------------------------
    # NEW METHOD TO FIX THE ERROR
    # -------------------------------------------------------------
    def upload_pdf(self, file: UploadFile, folder: str = "documents/pdfs") -> Optional[str]:
        """
        Upload a PDF file to S3 and return the URL
        """
        try:
            # Generate unique filename
            # Enforce .pdf extension for safety, though it should be passed correctly
            file_extension = 'pdf'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Create S3 key with folder structure
            s3_key = f"{folder}/{datetime.now().strftime('%Y/%m/%d')}/{unique_filename}"
            
            # Upload file to S3
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    # Use 'application/pdf' explicitly
                    'ContentType': 'application/pdf',
                    'ACL': 'public-read'  # Make file publicly accessible
                }
            )
            
            # Return the full URL
            return f"{self.base_url}/{s3_key}"
            
        except ClientError as e:
            print(f"Error uploading PDF to S3: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error uploading PDF: {e}")
            return None
    # -------------------------------------------------------------

    def upload_image(self, file: UploadFile, folder: str = "news/images") -> Optional[str]:
        """
        Upload an image file to S3 and return the URL
        """
        try:
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Create S3 key with folder structure
            s3_key = f"{folder}/{datetime.now().strftime('%Y/%m/%d')}/{unique_filename}"
            
            # Upload file to S3
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': file.content_type,
                    'ACL': 'public-read'  # Make image publicly accessible
                }
            )
            
            # Return the full URL
            return f"{self.base_url}/{s3_key}"
            
        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def delete_image(self, image_url: str) -> bool:
        """
        Delete an image from S3 given its URL
        """
        try:
            # Extract S3 key from URL
            s3_key = image_url.replace(f"{self.base_url}/", "")
            
            # Delete object from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
            
        except ClientError as e:
            print(f"Error deleting from S3: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

# Create singleton instance
s3_service = S3Service()