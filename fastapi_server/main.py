import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "langgraph_server")))

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from exceptions.base import AppException
from exceptions.handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    unexpected_exception_handler,
)

from api.v1.api import v1_router

from db.base import Base
from db.session import engine

from models import store_model # LangGraph DB 연결용 유지

Base.metadata.create_all(bind = engine)

from fastapi.middleware.cors import CORSMiddleware
from core.storage import init_storage
from contextlib import asynccontextmanager

#앱 실행 전후 동작 로직 
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_storage()
    except Exception as e:
        print(f"[WARNING] MinIO/S3 connection failed (server will continue): {e}")
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/v1")          # 신버전 라우터 (dx / ax / mx)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unexpected_exception_handler)

from fastapi.staticfiles import StaticFiles
import os

# 프론트엔드 정적 파일 서빙
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
