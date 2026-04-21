from langgraph_sdk import get_client


client = get_client(url = "http://127.0.0.1:2024")



async def run_ocr_agent(image_b64: str, user_language: str) -> dict:

    #ocr_agent 호출
    run = await client.runs.wait(
        thread_id=None,
        assistant_id="ocr_agent",
        input={
            "image_b64": image_b64,
            "user_language": user_language
        }
    )

    # runs.wait()는 최종 State를 dict로 반환
    ocr_result = run["ocr_result"]

    return ocr_result