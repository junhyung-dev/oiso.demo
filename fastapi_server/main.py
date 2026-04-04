import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "langgraph_server")))

from fastapi import FastAPI
from api.v1.api import api_router

from db.base import Base
from db.session import engine

from models import post_model
from models import chat_message_model
from models import chat_session_model
from models import store_model

Base.metadata.create_all(bind = engine)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1") 

from fastapi.staticfiles import StaticFiles
import os

# 프론트엔드 정적 파일 서빙
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
