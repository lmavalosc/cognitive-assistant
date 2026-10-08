"""Capa 4: Orquestación del Grafo Cognitivo con LangGraph.

Conecta la Memoria Persistente (Capa 5 / mem0) con el Gateway LLM (Plano A / LiteLLM)
para ejecutar ciclos de percepción, deliberación y consolidación de memoria.
"""

from typing import Any, Dict, List, Optional
from langgraph.graph import END, START, StateGraph

from cognitive_assistant.modules.c4_executive.state import CognitiveState
from cognitive_assistant.modules.c5_memory.service import get_memory_service
from cognitive_assistant.shared.infrastructure.llm import get_llm_gateway
from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id

logger = get_logger("cognitive_assistant.executive.graph")


async def retrieve_memories_node(state: CognitiveState) -> Dict[str, Any]:
    """Nodo 1: Recupera contexto y recuerdos persistentes del usuario desde Capa 5."""
    user_id = state.get("user_id", "default_user")
    query = state.get("input_message", "")
    trace_id = state.get("trace_id") or get_trace_id()

    logger.info("Nodo [Recuperar Memoria]: buscando contexto para '%s'", user_id)

    memory_service = get_memory_service()
    raw_memories = await memory_service.search(query=query, user_id=user_id, limit=3)

    formatted_memories: List[str] = []
    for item in raw_memories:
        text = item.get("memory") or item.get("text") or str(item)
        formatted_memories.append(text)

    return {
        "context_memories": formatted_memories,
        "status": "context_retrieved",
        "trace_id": trace_id,
    }


async def deliberate_and_plan_node(state: CognitiveState) -> Dict[str, Any]:
    """Nodo 2: Delibera, formula un plan cognitivo y genera respuesta vía LiteLLM."""
    input_message = state.get("input_message", "")
    memories = state.get("context_memories", [])
    trace_id = state.get("trace_id") or get_trace_id()

    logger.info("Nodo [Deliberación y Plan]: formulando respuesta cognitiva")

    context_str = "\n- ".join(memories) if memories else "Sin recuerdos previos relevantes."
    system_prompt = (
        "Eres el Asistente Cognitivo Modular (Tronco Encefálico + Ejecutivo Cognitivo). "
        "Tu objetivo es brindar respuestas precisas, conscientes del contexto y estructuradas.\n\n"
        f"Contexto/Recuerdos relevantes del usuario:\n- {context_str}\n\n"
        "Formula un razonamiento reflexivo y conciso."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_message},
    ]

    llm_gateway = get_llm_gateway()
    llm_result = await llm_gateway.acompletion(messages=messages)
    response_text = llm_result.get("content", "")

    # Plan mínimo de deliberación
    plan = [
        "1. Ingesta y análisis del estímulo sensorial.",
        f"2. Contextualización con {len(memories)} recuerdo(s) previos.",
        "3. Inferencia de respuesta estructurada.",
        "4. Consolidación de nueva memoria.",
    ]

    return {
        "intent": "cognitive_query",
        "plan": plan,
        "response": response_text,
        "status": "deliberated",
        "trace_id": trace_id,
    }


async def consolidate_memory_node(state: CognitiveState) -> Dict[str, Any]:
    """Nodo 3: Consolida la experiencia en la Memoria Persistente (Capa 5 / mem0)."""
    user_id = state.get("user_id", "default_user")
    input_message = state.get("input_message", "")
    response = state.get("response", "")
    trace_id = state.get("trace_id") or get_trace_id()

    logger.info("Nodo [Consolidación]: almacenando experiencia para '%s'", user_id)

    memory_service = get_memory_service()
    memory_content = f"Usuario: {input_message} | Asistente: {response}"
    await memory_service.add(
        content=memory_content,
        user_id=user_id,
        metadata={"trace_id": trace_id, "type": "dialogue_consolidation"},
    )

    return {
        "status": "completed",
        "trace_id": trace_id,
    }


def build_cognitive_graph() -> Any:
    """Construye y compila el StateGraph de LangGraph para el Ejecutivo Cognitivo."""
    builder = StateGraph(CognitiveState)

    # Añadir nodos
    builder.add_node("retrieve_memories", retrieve_memories_node)
    builder.add_node("deliberate_and_plan", deliberate_and_plan_node)
    builder.add_node("consolidate_memory", consolidate_memory_node)

    # Añadir aristas deterministas de flujo
    builder.add_edge(START, "retrieve_memories")
    builder.add_edge("retrieve_memories", "deliberate_and_plan")
    builder.add_edge("deliberate_and_plan", "consolidate_memory")
    builder.add_edge("consolidate_memory", END)

    return builder.compile()


_compiled_graph: Optional[Any] = None


def get_compiled_graph() -> Any:
    """Retorna la instancia compilada del grafo cognitivo."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_cognitive_graph()
    return _compiled_graph


async def execute_cognitive_cycle(
    message: str,
    user_id: str = "default_user",
    metadata: Optional[Dict[str, Any]] = None,
) -> CognitiveState:
    """
    Punto de entrada para ejecutar un ciclo cognitivo completo a través de LangGraph.
    """
    trace_id = get_trace_id()
    graph = get_compiled_graph()

    initial_state: CognitiveState = {
        "trace_id": trace_id,
        "user_id": user_id,
        "input_message": message,
        "context_memories": [],
        "intent": "pending",
        "plan": [],
        "response": "",
        "status": "started",
        "metadata": metadata or {},
    }

    logger.info("Iniciando ciclo cognitivo en LangGraph para trace_id=%s", trace_id)
    final_state = await graph.ainvoke(initial_state)
    logger.info("Ciclo cognitivo completado con status='%s'", final_state.get("status"))

    return final_state
