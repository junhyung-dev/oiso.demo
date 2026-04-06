import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.chat_session_model import ChatSession
from models.chat_message_model import ChatMessage
from langchain_core.messages import HumanMessage, AIMessage

# 서버 분리 통신: langgraph_sdk를 활용한 HTTP 클라이언트 접속
from langgraph_sdk import get_sync_client

def get_session_messages(db: Session, session_id: int) -> list[ChatMessage]:
    stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id.asc())
    return db.scalars(stmt).all()


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
    
    # 우선 DB에 유저 메시지를 먼저 저장해서 대화 목록(history)에 반영되도록 함
    save_message(db, session_id, "user", user_message)
    langgraph_thread_id = session.langgraph_thread_id
    
    # 기존 기록 불러오기 -> thread는 문맥을 유지하기 때문에 이제 불러올 필요는 없을듯
    # history = get_session_messages(db, session_id)
    
    # 2. HTTP 기반 LangGraph 서버(REST API) 클라이언트 연결
    client = get_sync_client(url="http://127.0.0.1:2024")
    

    # LangGraph Server에 보낼 페이로드
    # 기존: history message 전체 전달
    # 최신: 이제는 최신 user 메세지만 전달
    # messages_payload = [{"role": msg.role, "content": msg.content} for msg in history]
    messages_payload = [{"role": "user", "content": user_message}]

    # 3. LangGraph서버(agent)에 추론 요청(runs)을 생성하고 끝날 때까지 대기
    result = client.runs.wait(
        thread_id=langgraph_thread_id,
        assistant_id="agent",
        input={
            "messages": messages_payload,
            "client_lat": client_lat,
            "client_lng": client_lng,
            "user_language": user_language
        }
    )
    
    # 4. 결론 반환
    # 스레드가 처리 완료된 후 최신 상태(state)를 가져와서 가장 마지막 AIMessage 값을 가져옴
    thread_state = client.threads.get_state(langgraph_thread_id)
    final_answer = thread_state["values"]["messages"][-1]["content"]

    # 5. DB 저장
    save_message(db, session_id, "assistant", final_answer)
    
    return final_answer


def create_chat_session(db: Session, title: str | None = None) -> ChatSession:

    #채팅 세션 만들때, langgraph thread를 발급받아 DB에 함께 저장 (1대1 매핑으로)
    new_session = ChatSession(title=title)
    
    client = get_sync_client(url="http://127.0.0.1:2024")
    thread = client.threads.create()
    new_session.langgraph_thread_id = thread["thread_id"]

    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

def get_chat_session(db: Session, session_id: int) -> ChatSession | None:
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    return db.scalar(stmt)
