# app/schemas/upload.py
from pydantic import BaseModel, Field, validator

class MarkerResponse(BaseModel):
    """
    마커 응답용 스키마
    """
    id: int
    category: str
    latitude: float
    longitude: float

    class Config:
        orm_mode = True

class MarkerCreateValidation(BaseModel):
    latitude: float = Field(..., description="위도는 소수점으로 옵니다.")
    longitude: float = Field(..., description="경도는 소수점으로 옵니다.")
    
    @validator("latitude")
    def validate_latitude(cls, v):
        if not (-90.0 <= v <= 90.0):
            raise ValueError("위도는 지구상에 존재할 수 없는 값입니다 (-90 ~ 90).")
        return v
        
    @validator("longitude")
    def validate_longitude(cls, v):
        if not (-180.0 <= v <= 180.0):
            raise ValueError("경도는 지구상에 존재할 수 없는 값입니다 (-180 ~ 180).")
        return v
