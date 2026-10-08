"""Capa 4: Orquestación del Grafo Cognitivo con LangGraph.

Conecta la Memoria Persistente (Capa 5 / mem0) con el Gateway LLM (Plano A / LiteLLM)
para ejecutar ciclos de percepción, deliberación y consolidación de memoria.
"""

from typing import Any, Dict, List, Optional
from langgraph.graph import END, START, StateGraph

from cognitive_assistant.modules.c4_executive.state import CognitiveState
from cognitive_assistant.modules.c4_executive.working_memory import WorkingMemoryManager
from cognitive_assistant.modules.c5_memory.service import get_memory_service
from cognitive_assistant.shared.infrastructure.llm import get_llm_gateway
from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id

logger = get_logger("cognitive_assistant.executive.graph")


async def retrieve_memories_node(state: CognitiveState) -> Dict[str, Any]:
    """Nodo 1: Recupera contexto semántico (C5 / mem0) y turnos conversacionales recientes (Redis WM)."""
    user_id = state.get("user_id", "default_user")
    session_id = state.get("session_id", "default_session")
    query = state.get("input_message", "")
    trace_id = state.get("trace_id") or get_trace_id()

    logger.info("Nodo [Recuperar Memoria]: buscando contexto para user_id='%s', session_id='%s'", user_id, session_id)

    # 1. Recuperar recuerdos semánticos de largo plazo (Capa 5)
    memory_service = get_memory_service()
    raw_memories = await memory_service.search(query=query, user_id=user_id, limit=3)

    formatted_memories: List[str] = []
    for item in raw_memories:
        text = item.get("memory") or item.get("text") or str(item)
        formatted_memories.append(text)

    # 2. Recuperar memoria de trabajo activa de corto plazo (Redis)
    recent_turn_records = await WorkingMemoryManager.get_recent_turns(session_id=session_id, limit=6)
    dialogue_history = [
        {"role": turn.role, "content": turn.content}
        for turn in recent_turn_records
    ]
    logger.info("Memoria de trabajo recuperada: %d turnos previos para sesión '%s'", len(dialogue_history), session_id)

    return {
        "context_memories": formatted_memories,
        "dialogue_history": dialogue_history,
        "status": "context_retrieved",
        "trace_id": trace_id,
    }


async def deliberate_and_plan_node(state: CognitiveState) -> Dict[str, Any]:
    """Nodo 2: Delibera, formula plan cognitivo y genera respuesta vía LiteLLM con contexto y working memory."""
    input_message = state.get("input_message", "")
    memories = state.get("context_memories", [])
    history = state.get("dialogue_history", [])
    trace_id = state.get("trace_id") or get_trace_id()

    logger.info("Nodo [Deliberación y Plan]: formulando respuesta cognitiva (turnos en historial=%d)", len(history))

    context_str = "\n- ".join(memories) if memories else "Sin recuerdos persistentes previos relevantes."
    system_prompt = (
        "Eres el Asistente Cognitivo Modular (Tronco Encefálico + Ejecutivo Cognitivo). "
        "Tu objetivo es brindar respuestas precisas, coherentes, conscientes del contexto de la conversación.\n\n"
        f"Recuerdos persistentes del usuario:\n- {context_str}\n\n"
        "Formula un razonamiento reflexivo, estructurado y mantén la continuidad conversacional."
    )

    # Construir historial de mensajes para el LLM
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

    # Inyectar turnos previos de la memoria de trabajo de Redis
    for turn in history:
        messages.append({"role": turn["role"], "content": turn["content"]})

    # Inyectar turno actual del usuario
    messages.append({"role": "user", "content": input_message})

    llm_gateway = get_llm_gateway()
    llm_result = await llm_gateway.acompletion(messages=messages)
    response_text = llm_result.get("content", "")

    plan = [
        "1. Ingesta y análisis del estímulo sensorial.",
        f"2. Contextualización con {len(memories)} recuerdo(s) semánticos y {len(history)} turnos en memoria de trabajo.",
        "3. Inferencia de respuesta estructurada.",
        "4. Consolidación de memoria persistente y de trabajo.",
    ]

    return {
        "intent": "cognitive_query",
        "plan": plan,
        "response": response_text,
        "status": "deliberated",
        "trace_id": trace_id,
    }


async def consolidate_memory_node(state: CognitiveState) -> Dict[str, Any]:
    """Nodo 3: Consolida la experiencia en la Memoria Persistente (Mem0) y Memoria de Trabajo (Redis)."""
    user_id = state.get("user_id", "default_user")
    session_id = state.get("session_id", "default_session")
    input_message = state.get("input_message", "")
    response = state.get("response", "")
    trace_id = state.get("trace_id") or get_trace_id()

    logger.info("Nodo [Consolidación]: actualizando memoria de trabajo en Redis para sesión '%s'", session_id)

    # 1. Persistir turnos en Memoria de Trabajo activa (Redis)
    await WorkingMemoryManager.append_turn(
        session_id=session_id,
        role="user",
        content=input_message,
        trace_id=trace_id,
    )
    await WorkingMemoryManager.append_turn(
        session_id=session_id,
        role="assistant",
        content=response,
        trace_id=trace_id,
    )

    # 2. Persistir en Memoria Semántica de Largo Plazo (Capa 5 / mem0)
    memory_service = get_memory_service()
    memory_content = f"Usuario: {input_message} | Asistente: {response}"
    await memory_service.add(
        content=memory_content,
        user_id=user_id,
        metadata={"trace_id": trace_id, "session_id": session_id, "type": "dialogue_consolidation"},
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
    session_id: str = "default_session",
    metadata: Optional[Dict[str, Any]] = None,
) -> CognitiveState:
    """
    Punto de entrada para ejecutar un ciclo cognitivo completo a través de LangGraph
    con retención de memoria de trabajo en Redis.
    """
    trace_id = get_trace_id()
    graph = get_compiled_graph()

    initial_state: CognitiveState = {
        "trace_id": trace_id,
        "user_id": user_id,
        "session_id": session_id,
        "input_message": message,
        "context_memories": [],
        "dialogue_history": [],
        "active_goal": None,
        "intent": "pending",
        "plan": [],
        "response": "",
        "status": "started",
        "metadata": metadata or {},
    }

    logger.info("Iniciando ciclo cognitivo en LangGraph para trace_id=%s, session_id=%s", trace_id, session_id)
    final_state = await graph.ainvoke(initial_state)
    logger.info("Ciclo cognitivo completado con status='%s'", final_state.get("status"))

    return final_state

