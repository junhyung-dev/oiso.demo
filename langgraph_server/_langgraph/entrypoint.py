# (c) 2026 oiso.ai
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from _langgraph.tools.db_tools import search_nearby_stores
from _langgraph.llm_configs.sysmsg import get_query_enhancer_prompt, get_main_agent_prompt

# .env 로드
load_dotenv("../.env")

# 1. State 정의 (자연어 강화 단어 저장용 필드 추가)
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    client_lat: float
    client_lng: float
    user_language: str
    enhanced_query: str  # 쿼리 강화 에이전트가 뽑아낸 단일 태그(명사) 저장칸

# 2. 로컬 LLM 초기화
model = ChatOpenAI(model="gpt-4.1-mini", temperature=0.7)
# 쿼리 추출은 temperature 0 권장 (환각 최소화)
query_model = ChatOpenAI(model="gpt-4.1-mini", temperature=0.0) 

# 툴 바인딩
tools = [search_nearby_stores]
model_with_tools = model.bind_tools(tools)
tool_node = ToolNode(tools)


# ----------------- 노드(Node) 정의 -----------------

# 3-1. 쿼리 강화 노드 (Query Enhancer - 선행 에이전트)
def call_query_enhancer(state: AgentState):
    messages = state["messages"]
    
    # 마지막 사용자 메시지(HumanMessage)만 추출하여 노이즈 제거
    user_input = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_input = msg.content
            break
            
    # LLM에게 쿼리의 핵심 단어 정제를 요청 (프롬프트 주입)
    sys_msg = get_query_enhancer_prompt()
    enhancer_msg = [sys_msg, HumanMessage(content=user_input)]
    
    # 아주 짧은 단일 키워드(예: "떡볶이")를 반환받음
    response = query_model.invoke(enhancer_msg)
    
    # LLM이 도출한 단일 태그를 기존 messages 대화 목록에 섞지 않고,
    # 오직 AgentState의 'enhanced_query' 보관함에만 깔끔하게 저장하여 전달
    return {"enhanced_query": response.content.strip()}

# 3-2. 메인 노드 (도구 사용 및 답변)
def call_main_agent(state: AgentState):
    user_lang = state.get("user_language", "English")
    # 앞단에서 전해준 쿼리를 꺼냄
    enhanced_q = state.get("enhanced_query", "")
    
    sys_msg = get_main_agent_prompt(user_lang, enhanced_q)
    
    messages = [sys_msg] + [m for m in state["messages"] if not isinstance(m, SystemMessage)]
    
    response = model_with_tools.invoke(messages)
    
    # 툴 호출 시 좌표 강제 삽입 방어 로직
    if getattr(response, 'tool_calls', None):
        for tool_call in response.tool_calls:
            if tool_call["name"] == "search_nearby_stores":
                tool_call["args"]["lat"] = state.get("client_lat", 0.0)
                tool_call["args"]["lng"] = state.get("client_lng", 0.0)
                
    return {"messages": [response]}


# ----------------- 라우팅 및 그래프 설정 -----------------

def should_continue(state: AgentState) -> Literal["tools", END]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if getattr(last_message, 'tool_calls', None):
        return "tools"
    
    return END

workflow = StateGraph(AgentState)

# 노드 3대장 등록
workflow.add_node("query_enhancer", call_query_enhancer)
workflow.add_node("main_agent", call_main_agent)
workflow.add_node("tools", tool_node)

# 스타트(입구) -> 무조건 '쿼리 강화' 선행 -> '메인 에이전트'
workflow.add_edge(START, "query_enhancer")
workflow.add_edge("query_enhancer", "main_agent")

workflow.add_conditional_edges(
    "main_agent",
    should_continue,
    {
        "tools": "tools",
        END: END 
    }
)

# 툴을 실행하고 나면, 그 결괏값을 다시 메인 에이전트에게 줘서 번역 답변을 만들도록 라우팅 (Single Agent Loop 연장선)
workflow.add_edge("tools", "main_agent")

app = workflow.compile()