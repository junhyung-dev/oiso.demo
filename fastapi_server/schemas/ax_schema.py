from pydantic import BaseModel
from typing import List


# ─── /v1/ax/chat ────────────────────────────────────────────────

class ChatV2Request(BaseModel):
    uuid: str                  # 대화 세션 식별 UUID (Base64)
    user_added_message: str    # 유저 메시지


class ChatV2Response(BaseModel):
    response: str              # AI 응답 텍스트 (또는 성공/실패 메시지)


# ─── /v1/ax/pic_n_order ─────────────────────────────────────────

class MenuInformation(BaseModel):
    number: int
    text_in_original_language: str
    text_in_user_language: str
    price: int


class OCRInformation(BaseModel):
    menus: List[MenuInformation]
    user_language: str
    original_language: str


class PicNOrderResponse(BaseModel):
    response: str
    ocr_structure: OCRInformation | None = None
