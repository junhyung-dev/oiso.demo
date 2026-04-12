from fastapi import APIRouter, File, UploadFile, Form
from typing import List

from schemas.ax_schema import (
    ChatV2Request,
    ChatV2Response,
    MenuInformation,
    OCRInformation,
    PicNOrderResponse,
)

router = APIRouter()


@router.post("/chat", response_model=ChatV2Response)
async def chat_v2(request: ChatV2Request):
    """
    유저 메시지를 LangGraph Chat Agent로 전달하고 AI 응답을 반환합니다.

    - 현재: 더미 응답 반환
    - 추후: LangGraph HTTP 요청 + DB 저장 (UserMessage / AIMessage)
    """
    # TODO: uuid로 ChatSession 조회/생성 → LangGraph httpx 요청 → DB 저장
    dummy_reply = (
        f"[더미 응답] uuid={request.uuid} | "
        f"메시지 수신: '{request.user_added_message}'"
    )
    return ChatV2Response(response=dummy_reply)


@router.post("/pic_n_order", response_model=PicNOrderResponse)
async def pic_n_order(
    uuid: str = Form(...),
    user_language: str = Form(...),
    pics: List[UploadFile] = File(...),
):
    """
    메뉴판 사진을 OCR Agent로 전달하여 구조화된 메뉴 정보를 반환합니다.

    - 현재: 더미 OCR 결과 반환
    - 추후: 이미지 base64 인코딩 → LangGraph OCR Agent 요청 → OCRInformation 파싱
    """
    # TODO: 이미지 base64 인코딩 → LangGraph OCR Agent 요청
    dummy_ocr = OCRInformation(
        user_language=user_language,
        original_language="ko",
        menus=[
            MenuInformation(
                number=1,
                text_in_original_language="더미 메뉴",
                text_in_user_language="Dummy Menu",
                price=10000,
            )
        ],
    )
    return PicNOrderResponse(
        response="success (dummy)",
        ocr_structure=dummy_ocr,
    )
