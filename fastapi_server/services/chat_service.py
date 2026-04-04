import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.chat_session_model import ChatSession
from models.chat_message_model import ChatMessage
from langchain_core.messages import HumanMessage, AIMessage

# 서버 분리 통신: langgraph_server 모듈을 찾을 수 있도록 환경 변수 추가 후 import (동일 Host의 경우를 상정한 로컬 프로시저 호출 방식)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from langgraph_server._langgraph.entrypoint import app as langgraph_app


def get_session_messages(db: Session, session_id: int) -> list[ChatMessage]:
    stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id.asc())
    return db.scalars(stmt).all()

def build_langchain_message(history: list[ChatMessage], current_user_message: str) -> list:
    messages = []
    for msg in history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))
            
    messages.append(HumanMessage(content=current_user_message))
    return messages

def save_message(db: Session, session_id: int, role: str, content: str) -> ChatMessage:
    message = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def generate_answer(db: Session, session_id: int, user_message: str, client_lat: float, client_lng: float, user_language: str) -> str:
    # 1. 채팅 세션있는지 확인
    session = get_chat_session(db, session_id)
    if not session:
        raise ValueError("해당 session_id의 대화방이 존재하지 않습니다.")
    
    # 2. 기존 기록 불러오기 및 LangChain 규격화
    history = get_session_messages(db, session_id)
    messages = build_langchain_message(history, user_message)
    
    # 3. LangGraph 서버 호출 (State 통째로 주입)
    state = {
        "messages": messages,
        "client_lat": client_lat,
        "client_lng": client_lng,
        "user_language": user_language
    }
    
    # MSA 관점에서 HTTP(httpx) 호출을 권장하나 임시로 Local Procedure Call 방식으로 직접 연동합니다.
    result = langgraph_app.invoke(state)
    
    # 4. 결론 반환
    final_answer = result["messages"][-1].content

    # 5. DB 저장
    save_message(db, session_id, "user", user_message)
    save_message(db, session_id, "assistant", final_answer)
    
    return final_answer


def create_chat_session(db: Session, title: str | None = None) -> ChatSession:
    new_session = ChatSession(title=title)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

def get_chat_session(db: Session, session_id: int) -> ChatSession | None:
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    return db.scalar(stmt)
