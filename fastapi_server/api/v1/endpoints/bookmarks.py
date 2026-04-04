from fastapi import APIRouter
from schemas.bookmark_schema import bookmarkCreate, bookmarkResponse
from services import bookmark_service
from typing import List

router = APIRouter()

@router.post("/", response_model=bookmarkResponse)
def create_bookmark(bookmark : bookmarkCreate):
    return bookmark_service.create_bookmark(bookmark)
    
    

@router.get("/", response_model=List[bookmarkResponse])
def get_bookmark():
    return bookmark_service.get_bookmarks()