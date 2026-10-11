"""Definición del estado cognitivo de trabajo para LangGraph."""
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class CognitiveState(TypedDict):
    """Estado activo durante el ciclo de deliberación del Ejecutivo Cognitivo."""

    trace_id: str
    user_id: str
    session_id: str
    input_message: str
    context_memories: List[str]
    dialogue_history: List[Dict[str, str]]
    active_goal: Optional[str]
    intent: str
    plan: List[str]
    response: str
    status: str
    metadata: Dict[str, Any]
    sensitive_data_filtered: Optional[bool]
    filter_reason: Optional[str]
    pending_tool_calls: Optional[List[Dict[str, Any]]]
    tool_results: Optional[List[Dict[str, Any]]]


