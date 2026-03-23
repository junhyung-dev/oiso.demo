# app/main.py
from fastapi import FastAPI
from app.api.endpoints import markers
from app.api.endpoints import chat
from app.core.database import engine, Base
from app.models import marker, photo

Base.metadata.create_all(bind=engine)

app = FastAPI(title="UD-AMG Traditional Market Mapper API", version="1.0.0")

app.include_router(markers.router, prefix="/api/markers", tags=["Markers"])
app.include_router(chat.router, prefix="/api/ai", tags=["AI 챗봇"])

@app.get("/")
def root_check():
    """
    서버가 잘 켜졌는지 브라우저에서 확인해볼 수 있는 아주 간단한 헬스체크용 엔드포인트.
    """
    return {"message": "지도 서버가 정상 가동중입니다! 환영합니다."}
