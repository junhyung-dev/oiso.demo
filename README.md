# oiso.demo — Backend

FastAPI + LangGraph 기반 AI 관광 안내 챗봇 백엔드

---

## 구조

```
oiso_back/
├── fastapi_server/    # 클라이언트 요청 관리, 세션/DB 연동, LangGraph 통신 역할
└── langgraph_server/  # LangGraph Agent를 서빙하는 API 서버
```

---

## 실행 방법

> **주의**: 프론트엔드/API를 정상적으로 이용하려면 두 개의 서버를 **각각 별도의 터미널에서 동시에** 실행해야 합니다.
> 실행 전, 루트 경로(`.venv`)의 가상환경을 반드시 활성화해주세요. (`source .venv/bin/activate`)

### 1. LangGraph 에이전트 서버 실행

이 서버는 FastAPI의 추론 요청을 받아 Agent 로직을 실행합니다. (기본 포트: 2024)

```bash
cd langgraph_server
langgraph dev
```

### 2. FastAPI 메인 서버 실행

프론트엔드와 직접 통신하며, 세션을 관리하고 LangGraph 서버에 요청을 위임합니다. (포트: 8000)

```bash
cd fastapi_server
uvicorn main:app --reload --port 8000
```

---

## 환경 변수

`langgraph_server`는 기본적으로 `fastapi_server`의 `.env` 환경변수를 공유해서 사용합니다. (`langgraph.json` 참고)

- `fastapi_server/.env` 에 `OPENAI_API_KEY` 등을 설정한 뒤 실행하세요.
