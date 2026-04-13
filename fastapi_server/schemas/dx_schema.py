from pydantic import BaseModel
from schemas.base_schema import BaseSuccessResponse


class PicUploadResponse(BaseSuccessResponse):
    picture_url: str = ""  # 업로드된 원본 이미지의 MinIO URL
