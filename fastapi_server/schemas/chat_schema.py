from pydantic import BaseModel, Field
from datetime import datetime

class ChatSessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    #field는 검사와, 부가정보를 더해주는 것 (default는 None이되, max_length는 255로 한정)

class ChatSessionResponse(BaseModel):
    id: int
    title : str | None
    created_at: datetime

    model_config = {"from_attributes" : True}
    
    
    
class ChatRequest(BaseModel):
    session_id: int
    message: str = Field(min_length=1, examples=["I saw people eating long red rice cakes, where can I get those nearby?"])
    client_lat: float = Field(default=35.8690, description="대구 동성로 인근 예시 위도")
    client_lng: float = Field(default=128.5930, description="대구 동성로 인근 예시 경도")
    user_language: str = Field(default="English")
#당장 모델한테서 온 답변을 표시하기 위함
class ChatResponse(BaseModel):
    session_id: int
    answer: str
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answer": "FastAPI는 API 서버 프레임워크이고, LangChain은 LLM 앱을 구성하는 라이브러리입니다."
                }
            ]
        }
    }
    
#대화기록을 DB에서 뽑아서 반환
class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime
    
    model_config = {"from_attributes": True}