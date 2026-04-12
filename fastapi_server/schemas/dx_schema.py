from pydantic import BaseModel


class PicUploadResponse(BaseModel):
    response: str          # "success" or "error"
    picture_url: str = ""  # 업로드된 원본 이미지의 MinIO URL
