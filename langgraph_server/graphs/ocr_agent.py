# (c) 2026 oiso.ai
from langgraph.graph import StateGraph, START, END
from states.ocr_state import OCRAgentState


def placeholder(state: OCRAgentState):
    """TODO: OCR 로직으로 교체"""
    return state


workflow = StateGraph(OCRAgentState)
workflow.add_node("placeholder", placeholder)
workflow.add_edge(START, "placeholder")
workflow.add_edge("placeholder", END)

graph = workflow.compile()
