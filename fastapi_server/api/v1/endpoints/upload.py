from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Dict
from schemas.upload_schema import FileUploadResponse
from services import upload_service

router = APIRouter()

@router.post("/", response_model=FileUploadResponse)
async def upload_file(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail = "파일명이 없습니다.")
    
    return upload_service.save_file(file)    
