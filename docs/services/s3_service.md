# S3 Service

Module: `app/services/s3_service.py`

## Methods (via singleton `s3_service`)
- `upload_pdf(file: UploadFile, folder="documents/pdfs") -> Optional[str]`
- `upload_image(file: UploadFile, folder="news/images") -> Optional[str]`
- `delete_image(image_url: str) -> bool`

Environment:
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET_NAME`

Example (FastAPI route):
```python
image_url = s3_service.upload_image(upload_file, folder="gallery")
if not image_url:
    raise HTTPException(500, "Upload failed")
```
