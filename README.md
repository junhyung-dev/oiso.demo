# oiso.demo — Backend

FastAPI + LangGraph 기반 AI 관광 안내 챗봇 백엔드

---

## 구조

```
종프_back/
├── fastapi_server/    # API 게이트웨이 (DB, 라우터, 인증 등)
└── langgraph_server/  # LangGraph 에이전트 서버
```

---

## 실행 방법

### 1. FastAPI 서버

```bash
cd fastapi_server
uvicorn main:app --reload --port 8000
```

### 2. LangGraph 서버

```bash
cd langgraph_server/_langgraph
langgraph dev --host 0.0.0.0 --port 13337
```

> 두 서버를 **동시에** 실행해야 정상 동작합니다.

---

## 환경 변수

각 서버 폴더의 `.env` 파일을 설정한 뒤 실행하세요.

- `fastapi_server/.env`
- `langgraph_server/.env`
