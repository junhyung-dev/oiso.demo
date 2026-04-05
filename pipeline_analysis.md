# OISO 백엔드 파이프라인 분석 리뷰

프로젝트 내에서 FastAPI 서버와 LangGraph 서버가 디렉토리 상으로는 분리되어 있지만, **FastAPI 서버만 실행해도 채팅 기능이 정상 작동하는 원인**과 **현재 전체 데이터 파이프라인 구조**에 대해 분석한 결과입니다.

## 1. FastAPI 서버 구동만으로 채팅이 작동하는 원인 분석

결론부터 말씀드리면, 현재 구조는 **진정한 마이크로서비스 아키텍처(MSA)나 서버 간 네트워크 통신 분리 상태가 아닙니다.** FastAPI 어플리케이션이 LangGraph 코드를 라이브러리처럼 직접 불러와 **단일 프로세스 내에서(In-Memory)** 실행하고 있습니다. 

### 상세 로직
1. **의존성 주입**: `fastapi_server/main.py`와 `fastapi_server/services/chat_service.py`를 보면, 최상단에서 `sys.path.append`를 통해 상위 폴더 및 `langgraph_server` 경로를 Python 시스템 패스에 강제로 주입합니다.
   ```python
   # fastapi_server/services/chat_service.py
   sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
   from langgraph_server._langgraph.entrypoint import app as langgraph_app
   ```
2. **로컬 프로시저 호출 (Local Procedure Call)**: 채팅 API(`generate_answer` 함수)가 호출될 때, HTTP 요청(예: `httpx.post()`)을 통해 독립된 LangGraph 서버와 통신하는 것이 아닙니다. 대신 Import해온 `langgraph_app` 객체의 `invoke()` 메서드를 동일 쓰레드/프로세스 내에서 직접 실행합니다.
   ```python
   # MSA 관점에서 HTTP(httpx) 호출을 권장하나 임시로 Local Procedure Call 방식으로 직접 연동합니다.
   result = langgraph_app.invoke(state)
   ```

**📝 시사점**: 코드는 분리해두었지만 실행 환경은 통합되어 있는 "모놀리식(Monolithic)" 상태입니다. 당장 작동하는 데는 문제가 없지만(실제로 로컬 테스트에는 편리함), 추후 트래픽 증가로 인해 LLM 에이전트 전용 서버만 스케일아웃(확장)해야 할 때는 HTTP API 혹은 gRPC 기반 연결로 코드를 수정해 주어야 합니다.

---

## 2. 현재 시스템 파이프라인 (Data Flow)

본 프로젝트(전통시장 자동 지도 완성 및 AI 에이전트 서비스)의 데이터 흐름은 크게 두 파트로 나뉩니다.

### A. 이미지 업로드 & 태깅 파이프라인 (현 프록시 단계)
1. **클라이언트 입력**: 사용자(웹/앱)가 상점이나 음식 사진과 함께 위치 정보(위도, 경도)를 전송합니다.
2. **FastAPI 접수 (`/api/v1/upload`)**: `upload_image_and_tag_proxy` 엔드포인트에서 데이터를 접수합니다.
3. **VLM 서버 연동 (Todo)**: 추후 이 이미지들을 외부 Vision-Language Model 서버로 전송하여 이미지를 분석 및 클러스터링합니다.
4. **DB 업데이트 (예정 패턴)**: VLM 서버가 분석을 마치면 그 결과를 바탕으로 메인 DB의 `Store` 테이블과 `Tag` 테이블 간 다대다 관계가 생성/업데이트 됩니다. 현재는 Mock Response만 반환하는 Proxy 구조입니다.

### B. AI 에이전트 채팅 파이프라인 (LangGraph 연계)
1. **DB 히스토리 로드**: 사용자가 질문을 던지면 `chat_service.py`가 RDBMS(현재 테스트용 SQLite, 적용시 PostgreSQL 등)의 `ChatMessage` 테이블에서 이전 대화 기록을 불러옵니다.
2. **LangChain 규격화**: 이를 `HumanMessage`와 `AIMessage` 규격의 배열로 변환합니다.
3. **LangGraph State 주입**: 대화 기록, 사용자 위치(위경도), 언어 설정을 `state` 객체에 묶어 `langgraph_app`에 던집니다.
4. **그래프 동작 (`_langgraph/entrypoint.py`)**:
   - **Step 1 - Query Enhancer (쿼리 강화)**: 별도의 낮은 Temperature를 가진 LLM(`gpt-4.1-mini`)이 사용자의 마지막 질문에서 "떡볶이", "김밥" 같은 핵심 명사 단일 태그(Keyword)만 추출하여 노이즈를 제거합니다.
   - **Step 2 - Main Agent**: 정제된 키워드를 바탕으로 메인 프롬프트가 구성되고, 메인 에이전트가 실행됩니다.
   - **Step 3 - Tools (`search_nearby_stores`)**: 에이전트가 주변 매장을 찾아야 한다고 판단하면 DB Tool이 실행됩니다. SQLAlchemy를 활용하여 DB의 `stores`와 `tags` 테이블 조인을 실행하고, 파이썬 기반 하버사인(Haversine) 거리 공식을 통해 반경 1km 이내 조건을 충족하는 상점 목록을 반환합니다.
   - **Step 4 - 최종 답변 반환**: 도구의 결괏값을 바탕으로 메인 에이전트(LLM)가 사용자의 설정 언어에 맞게 다듬어진 답변 문장을 생성하여 응답합니다.
5. **DB 저장**: 최종 생성된 유저와 어시스턴트의 대화가 `ChatMessage`로 저장되고 FastAPI 응답이 내려갑니다.

---

## 3. 요약 및 향후 개선 과제

현재의 **Directory Based Separation (디렉토리 분리) + Import Binding (직접 참조)** 패턴은 초기 개발 속도를 높이는데는 유리하나 배포 시 다음과 같은 문제 및 수정 지점이 존재합니다.

- **분산 환경 도입**: 현재의 로컬 프로시저(`langgraph_app.invoke()`) 방식 대신, LangGraph를 별도 포트(예: 8000번, 8001번)에서 HTTP 서버(예: FastAPI, LangServe) 기반 서비스로 돌리고, FastAPI 쪽에서는 비동기 HTTP Client(`httpx`)를 이용해 JSON API로 통신해야 시스템 부하를 분산시킬 수 있습니다.
- **의존성 충돌**: 현재 `fastapi_server`와 `langgraph_server`가 각각의 `requirements.txt`를 가지고 있음에도 한 프로세스에서 동작하므로, 추후 라이브러리 버전 충돌 위협이 존재합니다.
