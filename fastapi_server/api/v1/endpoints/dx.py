from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
from uuid import uuid4

from schemas.dx_schema import PicUploadResponse
from core.config import settings
from core.storage import get_s3_client
from services import dx_services

router = APIRouter()


@router.post("/upload_picture", response_model=PicUploadResponse)
async def upload_picture(image: UploadFile = File(...)):
    """
    사진 파일을 MinIO에 업로드하고 URL을 반환합니다.
    
    - 현재: 원본 이미지만 MinIO 업로드 후 URL 반환 (더미 구현)
    - 추후: lowres/highres 버전 생성 + DB 저장 + Redis 큐 적재
    """

    picture_url = dx_services.upload_picture(image)

    #성공한 응답만 반환함
    #핵심: picuploadrespons가 BaseSuccessResponse를 상속받았으므로 success=True가 자동 삽입됨
    return PicUploadResponse(picture_url=picture_url)

    
