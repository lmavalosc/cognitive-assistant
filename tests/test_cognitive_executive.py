import pytest
from cognitive_assistant.modules.c4_executive.graph import (
    build_cognitive_graph,
    execute_cognitive_cycle,
)
from cognitive_assistant.shared.telemetry.trace import set_trace_id


def test_build_cognitive_graph():
    """Verifica que el grafo de LangGraph compile correctamente."""
    graph = build_cognitive_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_execute_cognitive_cycle():
    """Verifica la ejecución del ciclo cognitivo completo a través del grafo."""
    set_trace_id("test-exec-trace-555")

    final_state = await execute_cognitive_cycle(
        message="¿Cuál es la estrategia de hoy?",
        user_id="user_exec_01",
    )

    assert final_state["status"] == "completed"
    assert "response" in final_state
    assert len(final_state["response"]) > 0
    assert len(final_state["plan"]) > 0
    assert final_state["trace_id"] == "test-exec-trace-555"
