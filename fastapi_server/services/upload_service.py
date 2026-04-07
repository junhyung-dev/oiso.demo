from uuid import uuid4
from fastapi import UploadFile
from pathlib import Path
from schemas.upload_schema import FileUploadResponse

from core.config import settings
from core.storage import get_s3_client




def save_file(file: UploadFile) -> FileUploadResponse:
    ext = Path(file.filename).suffix if file.filename else ""
    saved_name = f"{uuid4()}{ext}"


    # S3 클라이언트를 가져옴
    s3_client = get_s3_client()
    bucket_name = settings.MINIO_BUCKET_NAME

    # MinIO로 파일 데이터를 업로드함 참고: https://docs.aws.amazon.com/boto3/latest/guide/s3-uploading-files.html
    s3_client.upload_fileobj(
        file.file,
        bucket_name,
        saved_name,

        ExtraArgs={
            "ContentType": file.content_type,
        },
    )

    # 사진 볼수있는 URL주소 생성
    # 기본 URL 구조: 통신주소/버킷이름/파일이름
    file_url = f"{settings.MINIO_ENDPOINT_URL}/{bucket_name}/{saved_name}"

    return FileUploadResponse(
        original_filename = file.filename,
        saved_filename=saved_name,
        content_type=file.content_type,
        file_url=file_url

        
    )
