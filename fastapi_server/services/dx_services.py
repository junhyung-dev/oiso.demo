from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from core.config import settings
from core.storage import get_s3_client


#커스텀 예외
from exceptions.http import BadRequestException, StorageException


def upload_picture(image: UploadFile) -> str:
    """
    이미지를 S3(MinIO)에 업로드하고 URL 반환
    """

    if not image.filename:
        #이런식으로 Exception던지는게 가능
        raise BadRequestException(reason="업로드할 파일명이 존재하지 않습니다.")

    # 고유 파일명 생성
    ext = Path(image.filename).suffix
    saved_name = f"{uuid4()}{ext}"

    try:
        s3_client = get_s3_client()
        bucket_name = settings.MINIO_BUCKET_NAME

        # MinIO에 원본 이미지 업로드
        s3_client.upload_fileobj(
            image.file,
            bucket_name,
            saved_name,
            ExtraArgs={"ContentType": image.content_type or "application/octet-stream"},
        )

        # 접근 가능한 URL 생성: {endpoint}/{bucket}/{key}
        picture_url = f"{settings.MINIO_ENDPOINT_URL}/{bucket_name}/{saved_name}"

        return picture_url

    except Exception as e:
        raise StorageException(reason=f"파일 업로드에 실패했습니다. ({str(e)})")
        
