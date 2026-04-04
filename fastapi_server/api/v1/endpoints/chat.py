from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from db.session import get_db

from schemas.chat_schema import ChatRequest, ChatResponse, ChatMessageResponse, ChatSessionCreate, ChatSessionResponse
from services import chat_service

router = APIRouter()

db_session = Annotated[Session, Depends(get_db)]

#/chat
@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: db_session):
    try:
        
        answer = chat_service.generate_answer(
            db=db,
            session_id=request.session_id,
            user_message=request.message,
            client_lat=request.client_lat,
            client_lng=request.client_lng,
            user_language=request.user_language
        )
        return ChatResponse(session_id=request.session_id, answer=answer)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


#/chat/sessions
@router.post("/sessions", response_model=ChatSessionResponse)
def create_chat_session(request: ChatSessionCreate, db: db_session):
    return chat_service.create_chat_session(db, request.title)

#/chat/sessions/{session_id}/messages
@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def get_session_messages(session_id: int, db: db_session):
    session = chat_service.get_chat_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return chat_service.get_session_messages(db, session_id=session_id)