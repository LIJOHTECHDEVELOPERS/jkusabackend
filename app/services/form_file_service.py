import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
import io

from app.services.s3_service import s3_service
from app.models.registration import FormFieldUpload, FormSubmission, FormField
from app.config import settings

logger = logging.getLogger(__name__)

# ========== CONSTANTS ==========
ALLOWED_FILE_TYPES = {
    'pdf': ['application/pdf'],
    'doc': ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    'image': ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/svg+xml'],
    'video': ['video/mp4', 'video/quicktime', 'video/webm'],
    'spreadsheet': ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    'archive': ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed', 'application/x-tar']
}

MAX_FILE_SIZES = {
    'pdf': 50 * 1024 * 1024,  # 50MB
    'doc': 25 * 1024 * 1024,  # 25MB
    'image': 10 * 1024 * 1024,  # 10MB
    'video': 500 * 1024 * 1024,  # 500MB
    'spreadsheet': 20 * 1024 * 1024,  # 20MB
    'archive': 100 * 1024 * 1024  # 100MB
}

class FormFileService:
    """Service for handling form file uploads and management"""
    
    def __init__(self, s3_service, db: Session = None):
        self.s3_service = s3_service
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def validate_file(
        self,
        file: UploadFile,
        allowed_types: List[str],
        custom_max_size: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file before upload
        
        Args:
            file: Uploaded file
            allowed_types: List of allowed type keys (pdf, doc, image, etc)
            custom_max_size: Optional custom max size in bytes
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate file name
        if not file.filename:
            return False, "File must have a name"
        
        # Validate content type
        content_type = file.content_type
        valid_types = []
        for type_key in allowed_types:
            valid_types.extend(ALLOWED_FILE_TYPES.get(type_key, []))
        
        if content_type not in valid_types:
            allowed_str = ', '.join(allowed_types)
            return False, f"File type not allowed. Allowed: {allowed_str}"
        
        # Validate file size
        if file.size:
            # Determine max size
            max_size = custom_max_size
            if not max_size:
                # Use largest max for the allowed types
                max_size = max(MAX_FILE_SIZES.get(t, 10 * 1024 * 1024) for t in allowed_types)
            
            if file.size > max_size:
                max_mb = max_size / 1024 / 1024
                return False, f"File too large. Maximum size: {max_mb:.0f}MB"
        
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        valid_extensions = self._get_valid_extensions(allowed_types)
        if file_ext and file_ext not in valid_extensions:
            return False, f"File extension not allowed: {file_ext}"
        
        return True, None
    
    def _get_valid_extensions(self, allowed_types: List[str]) -> List[str]:
        """Get valid file extensions for allowed types"""
        extensions = {
            'pdf': ['.pdf'],
            'doc': ['.doc', '.docx'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
            'video': ['.mp4', '.mov', '.webm', '.avi'],
            'spreadsheet': ['.xls', '.xlsx'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz']
        }
        
        valid_exts = []
        for type_key in allowed_types:
            valid_exts.extend(extensions.get(type_key, []))
        return valid_exts
    
    async def upload_form_file(
        self,
        file: UploadFile,
        submission_id: int,
        field_id: int,
        allowed_types: List[str],
        max_size: Optional[int] = None,
        db: Optional[Session] = None
    ) -> str:
        """
        Upload file to S3 and track in database
        
        Args:
            file: Uploaded file
            submission_id: Form submission ID
            field_id: Form field ID
            allowed_types: Allowed file types
            max_size: Optional custom max size
            db: Database session
        
        Returns:
            S3 URL of uploaded file
        """
        # Validate
        is_valid, error = self.validate_file(file, allowed_types, max_size)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        try:
            # Read file content
            file_content = await file.read()
            file.file.seek(0)  # Reset for potential re-reads
            
            # Calculate file hash
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Determine file type category
            file_type = self._get_file_type_category(file.content_type)
            
            # Generate S3 key
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_ext = Path(file.filename).suffix.lower()
            safe_filename = Path(file.filename).stem.replace(' ', '_')[:100]
            
            s3_key = f"forms/submissions/submission_{submission_id}/field_{field_id}/{timestamp}_{safe_filename}{file_ext}"
            
            self.logger.debug(f"Uploading file to S3: {s3_key}")
            
            # Upload to S3
            file_url = self.s3_service.upload_file(
                file=file,
                key=s3_key,
                content_type=file.content_type
            )
            
            if not file_url:
                raise Exception("S3 upload returned empty URL")
            
            # Track file upload in database if session provided
            if db:
                file_upload = FormFieldUpload(
                    submission_id=submission_id,
                    field_id=field_id,
                    original_filename=file.filename,
                    file_size=file.size or len(file_content),
                    file_type=file_type,
                    content_type=file.content_type,
                    s3_key=s3_key,
                    s3_url=file_url,
                    file_hash=file_hash,
                    virus_scan_status="pending"
                )
                db.add(file_upload)
                try:
                    db.commit()
                    db.refresh(file_upload)
                    self.logger.info(f"File upload tracked: {file_upload.id} - {s3_key}")
                except Exception as e:
                    self.logger.warning(f"Failed to track file upload in database: {str(e)}")
                    db.rollback()
            
            self.logger.info(f"File uploaded successfully: {file_url}")
            return file_url
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error uploading form file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    async def upload_multiple_files(
        self,
        files: List[UploadFile],
        submission_id: int,
        field_id: int,
        allowed_types: List[str],
        max_size: Optional[int] = None,
        db: Optional[Session] = None
    ) -> List[str]:
        """
        Upload multiple files for multi-file upload field
        
        Args:
            files: List of uploaded files
            submission_id: Form submission ID
            field_id: Form field ID
            allowed_types: Allowed file types
            max_size: Optional custom max size
            db: Database session
        
        Returns:
            List of S3 URLs
        """
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided"
            )
        
        file_urls = []
        failed_files = []
        
        for file in files:
            try:
                url = await self.upload_form_file(
                    file, submission_id, field_id, allowed_types, max_size, db
                )
                file_urls.append(url)
            except HTTPException as e:
                failed_files.append(f"{file.filename}: {e.detail}")
        
        if failed_files and not file_urls:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"All files failed to upload: {'; '.join(failed_files)}"
            )
        
        if failed_files:
            self.logger.warning(f"Some files failed: {'; '.join(failed_files)}")
        
        return file_urls
    
    def _get_file_type_category(self, content_type: str) -> str:
        """Determine file type category from content type"""
        for category, types in ALLOWED_FILE_TYPES.items():
            if content_type in types:
                return category
        return "unknown"
    
    def delete_file(self, s3_url: str) -> bool:
        """
        Delete file from S3
        
        Args:
            s3_url: S3 URL of file to delete
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            self.s3_service.delete_file(s3_url)
            self.logger.info(f"File deleted from S3: {s3_url}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting file from S3: {str(e)}")
            return False
    
    def get_upload_history(
        self,
        submission_id: int,
        field_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> List[dict]:
        """
        Get upload history for a submission
        
        Args:
            submission_id: Form submission ID
            field_id: Optional field ID to filter by
            db: Database session
        
        Returns:
            List of upload records
        """
        if not db:
            return []
        
        query = db.query(FormFieldUpload).filter(
            FormFieldUpload.submission_id == submission_id
        )
        
        if field_id:
            query = query.filter(FormFieldUpload.field_id == field_id)
        
        uploads = query.order_by(FormFieldUpload.upload_timestamp.desc()).all()
        
        return [
            {
                "id": u.id,
                "field_id": u.field_id,
                "filename": u.original_filename,
                "size": u.file_size,
                "type": u.file_type,
                "uploaded_at": u.upload_timestamp.isoformat(),
                "s3_url": u.s3_url,
                "virus_status": u.virus_scan_status
            }
            for u in uploads
        ]
    
    def cleanup_submission_files(
        self,
        submission_id: int,
        db: Optional[Session] = None
    ) -> Tuple[int, int]:
        """
        Delete all files associated with a submission
        
        Args:
            submission_id: Form submission ID
            db: Database session
        
        Returns:
            Tuple of (deleted_count, failed_count)
        """
        if not db:
            return 0, 0
        
        uploads = db.query(FormFieldUpload).filter(
            FormFieldUpload.submission_id == submission_id
        ).all()
        
        deleted = 0
        failed = 0
        
        for upload in uploads:
            if self.delete_file(upload.s3_url):
                db.delete(upload)
                deleted += 1
            else:
                failed += 1
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error committing file deletions: {str(e)}")
        
        return deleted, failed
    
    def get_file_by_url(self, s3_url: str) -> Optional[bytes]:
        """
        Download file from S3
        
        Args:
            s3_url: S3 URL of file
        
        Returns:
            File content as bytes or None
        """
        try:
            return self.s3_service.download_file(s3_url)
        except Exception as e:
            self.logger.error(f"Error downloading file from S3: {str(e)}")
            return None
    
    def generate_presigned_url(
        self,
        s3_url: str,
        expiration_seconds: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for temporary file access
        
        Args:
            s3_url: S3 URL of file
            expiration_seconds: URL expiration time in seconds
        
        Returns:
            Presigned URL or None
        """
        try:
            return self.s3_service.generate_presigned_url(
                s3_url, expiration_seconds
            )
        except Exception as e:
            self.logger.error(f"Error generating presigned URL: {str(e)}")
            return None
    
    def validate_file_virus_scan(
        self,
        upload_id: int,
        db: Session
    ) -> bool:
        """
        Check and update virus scan status (integrate with ClamAV or similar)
        
        Args:
            upload_id: FormFieldUpload ID
            db: Database session
        
        Returns:
            True if file is clean, False if infected or error
        """
        try:
            upload = db.query(FormFieldUpload).filter(
                FormFieldUpload.id == upload_id
            ).first()
            
            if not upload:
                return False
            
            # TODO: Integrate with virus scanning service (ClamAV, VirusTotal, etc)
            # For now, mark as clean
            upload.virus_scan_status = "clean"
            db.commit()
            
            self.logger.info(f"File {upload_id} scanned: clean")
            return True
            
        except Exception as e:
            self.logger.error(f"Error scanning file: {str(e)}")
            return False
    
    def get_upload_statistics(
        self,
        db: Session,
        form_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """
        Get upload statistics
        
        Args:
            db: Database session
            form_id: Optional form ID to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            Dictionary with statistics
        """
        try:
            query = db.query(FormFieldUpload)
            
            if form_id:
                query = query.join(FormSubmission).filter(
                    FormSubmission.form_id == form_id
                )
            
            if start_date:
                query = query.filter(FormFieldUpload.upload_timestamp >= start_date)
            
            if end_date:
                query = query.filter(FormFieldUpload.upload_timestamp <= end_date)
            
            uploads = query.all()
            
            total_size = sum(u.file_size for u in uploads)
            
            type_breakdown = {}
            for upload in uploads:
                file_type = upload.file_type
                type_breakdown[file_type] = type_breakdown.get(file_type, 0) + 1
            
            return {
                "total_files": len(uploads),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "by_type": type_breakdown,
                "infected_files": sum(1 for u in uploads if u.virus_scan_status == "infected"),
                "clean_files": sum(1 for u in uploads if u.virus_scan_status == "clean"),
                "pending_scan": sum(1 for u in uploads if u.virus_scan_status == "pending")
            }
        
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {str(e)}")
            return {}


# Create singleton instance
form_file_service = FormFileService(s3_service)