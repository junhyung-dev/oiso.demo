import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# 상위 폴더의 .env (또는 해당 서버의 .env) 등을 로드합니다.
load_dotenv(".env")

# 방금 작성한 LangGraph의 메인 앱(app)을 불러옵니다.
from _langgraph.entrypoint import app

def run_test():
    print("🤖 --- LangGraph 파이프라인 독립 테스트 --- 🤖")
    print("시나리오: 외국인이 영어로 '긴 빨간 떡 파는 곳 찾아줘'라고 질문")
    
    # 1. 초기 메시지와 상태(State) 값 설정
    # 사용자의 (위도, 경도)는 대구 동성로 인근 좌표로 설정
    initial_state = {
        "messages": [HumanMessage(content="I saw people eating long red rice cakes, where can I get those nearby?")],
        "client_lat": 35.8690,
        "client_lng": 128.5930,
        "user_language": "English"
    }
    
    # 2. 랭그래프 실행 (invoke)
    print("\n[진행중] LangGraph가 에이전트들을 순차적으로 호출하여 결과를 추론하고 있습니다...\n")
    
    # stream 모드로 실행하면 각 노드(main -> tools -> translator)가 끝날 때마다 상태 변화를 추적할 수 있습니다.
    for step in app.stream(initial_state, stream_mode="updates"):
        for node_name, node_state in step.items():
            print(f">>> [완료된 노드: {node_name}]")
            # 맨 마지막에 추가된 메시지 확인
            latest_message = node_state["messages"][-1]
            
            if node_name == "main_agent":
                print("  💡 메인 에이전트가 툴 호출을 결심했습니다!")
                print("  (호출 도구명:", latest_message.tool_calls[0]['name'], "/ 전달 인자값:", latest_message.tool_calls[0]['args'], ")\n")
            
            elif node_name == "tools":
                print(f"  🔍 DB 검색 툴이 반환한 내용 (원시 데이터): \n  {latest_message.content}\n")
            
            elif node_name == "translator":
                print(f"  🗣️ 최종 번역/응답 에이전트의 답변 출력:\n  {latest_message.content}\n")
    
    print("✅ 테스트가 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    run_test()
