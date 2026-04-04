from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings


#DB와 실제 연결 통로 = engine
engine = create_engine(settings.DATABASE_URL)


#세션 생성 도구
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()