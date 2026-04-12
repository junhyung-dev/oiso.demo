from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
from uuid import uuid4

from schemas.dx_schema import PicUploadResponse
from core.config import settings
from core.storage import get_s3_client

router = APIRouter()


@router.post("/pic_upload", response_model=PicUploadResponse)
async def pic_upload(image: UploadFile = File(...)):
    """
    사진 파일을 MinIO에 업로드하고 URL을 반환합니다.
    
    - 현재: 원본 이미지만 MinIO 업로드 후 URL 반환 (더미 구현)
    - 추후: lowres/highres 버전 생성 + DB 저장 + Redis 큐 적재
    """
    if not image.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

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

        return PicUploadResponse(response="success", picture_url=picture_url)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"업로드 실패: {str(e)}")
