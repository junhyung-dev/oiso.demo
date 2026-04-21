# (c) 2026 oiso.ai
from langgraph.graph import StateGraph, START, END
from states.ocr_state import OCRAgentState
from nodes.ocr_nodes import call_ocr_node


# 그래프 조립
workflow = StateGraph(OCRAgentState)

workflow.add_node("ocr_agent", call_ocr_node)


#TODO: 흐름 강화
#현재는 START -> ocr_agent -> END의 형태
workflow.add_edge(START, "ocr_agent")
workflow.add_edge("ocr_agent", END)


graph = workflow.compile()
