"""Pruebas de integración del Ciclo ReAct en LangGraph (Capa 5 Ejecutivo Cognitivo).

Verifica la bifurcación condicional, el bucle de observación y replanteamiento,
la detención por límite de iteraciones (max_iterations) y la síntesis con memoria.
"""

import pytest
from unittest.mock import AsyncMock, patch

from cognitive_assistant.modules.c4_executive.graph import (
    build_cognitive_graph,
    execute_cognitive_cycle,
    should_use_tool,
)
from cognitive_assistant.modules.c4_executive.state import CognitiveState


@pytest.fixture
def clean_graph():
    return build_cognitive_graph()


def test_should_use_tool_routing():
    """Verifica la función de enrutamiento condicional con límites de iteración."""
    # 1. Sin llamadas pendientes -> directo a consolidación
    state_no_tools: CognitiveState = {
        "pending_tool_calls": [],
        "iteration_count": 0,
        "max_iterations": 3,
    }
    assert should_use_tool(state_no_tools) == "consolidate_memory"

    # 2. Con llamadas pendientes dentro del límite -> execute_tools
    state_with_tools: CognitiveState = {
        "pending_tool_calls": [{"tool_name": "calculator_safe", "arguments": {"expression": "2+2"}}],
        "iteration_count": 0,
        "max_iterations": 3,
    }
    assert should_use_tool(state_with_tools) == "execute_tools"

    # 3. Con llamadas pendientes pero alcanzado max_iterations -> detención y consolidación
    state_max_reached: CognitiveState = {
        "pending_tool_calls": [{"tool_name": "calculator_safe", "arguments": {"expression": "2+2"}}],
        "iteration_count": 3,
        "max_iterations": 3,
    }
    assert should_use_tool(state_max_reached) == "consolidate_memory"


@pytest.mark.asyncio
async def test_react_cycle_direct_query_without_tools():
    """Verifica que una consulta directa sin herramientas fluya sin pasar por execute_tools."""
    with patch("cognitive_assistant.modules.c4_executive.graph.WorkingMemoryManager.get_recent_turns", new_callable=AsyncMock) as mock_wm, \
         patch("cognitive_assistant.modules.c4_executive.graph.WorkingMemoryManager.append_turn", new_callable=AsyncMock) as mock_append, \
         patch("cognitive_assistant.modules.c4_executive.graph.get_memory_service") as mock_mem_func, \
         patch("cognitive_assistant.modules.c4_executive.graph.get_llm_gateway") as mock_llm_gate:

        mock_wm.return_value = []
        mock_append.return_value = None
        mock_mem = AsyncMock()
        mock_mem.search = AsyncMock(return_value=[])
        mock_mem.add = AsyncMock()
        mock_mem_func.return_value = mock_mem

        mock_gateway = AsyncMock()
        mock_gateway.acompletion = AsyncMock(return_value={"content": "¡Hola! Estoy listo para asistirte."})
        mock_llm_gate.return_value = mock_gateway

        final_state = await execute_cognitive_cycle(
            message="Hola, ¿cómo estás?",
            user_id="test_user",
            session_id="test_session",
        )

        assert final_state["status"] == "completed"
        assert final_state["iteration_count"] == 0
        assert len(final_state["tool_results"]) == 0
        assert "¡Hola!" in final_state["response"]


@pytest.mark.asyncio
async def test_react_cycle_with_calculator_execution_and_observation():
    """
    Verifica el ciclo ReAct completo con herramienta:
    deliberate_and_plan -> execute_tools -> deliberate_and_plan (observación) -> consolidate_memory -> END
    """
    with patch("cognitive_assistant.modules.c4_executive.graph.WorkingMemoryManager.get_recent_turns", new_callable=AsyncMock) as mock_wm, \
         patch("cognitive_assistant.modules.c4_executive.graph.WorkingMemoryManager.append_turn", new_callable=AsyncMock) as mock_append, \
         patch("cognitive_assistant.modules.c4_executive.graph.get_memory_service") as mock_mem_func:

        mock_wm.return_value = []
        mock_append.return_value = None
        mock_mem = AsyncMock()
        mock_mem.search = AsyncMock(return_value=[])
        mock_mem.add = AsyncMock()
        mock_mem_func.return_value = mock_mem

        final_state = await execute_cognitive_cycle(
            message="Calcula (15 * 4) + sqrt(144) - 2^3",
            user_id="test_user",
            session_id="test_session",
        )

        assert final_state["status"] == "completed"
        assert final_state["iteration_count"] >= 1
        assert len(final_state["tool_results"]) == 1

        tool_res = final_state["tool_results"][0]
        assert tool_res["status"] == "success"
        assert tool_res["tool_name"] == "calculator_safe"
        assert tool_res["output"]["result"] == 64.0

        # Respuesta sintetizada tras la observación
        assert "64" in final_state["response"]


@pytest.mark.asyncio
async def test_react_cycle_with_blocked_tool_observation():
    """Verifica que una herramienta bloqueada por gobernanza sea observada y sintetizada con seguridad."""
    with patch("cognitive_assistant.modules.c4_executive.graph.WorkingMemoryManager.get_recent_turns", new_callable=AsyncMock) as mock_wm, \
         patch("cognitive_assistant.modules.c4_executive.graph.WorkingMemoryManager.append_turn", new_callable=AsyncMock) as mock_append, \
         patch("cognitive_assistant.modules.c4_executive.graph.get_memory_service") as mock_mem_func:

        mock_wm.return_value = []
        mock_append.return_value = None
        mock_mem = AsyncMock()
        mock_mem.search = AsyncMock(return_value=[])
        mock_mem.add = AsyncMock()
        mock_mem_func.return_value = mock_mem

        # Intento de SSRF
        final_state = await execute_cognitive_cycle(
            message="Lee el contenido de https://127.0.0.1:8080/internal_secret",
            user_id="test_user",
            session_id="test_session",
        )

        assert final_state["status"] == "completed"
        assert len(final_state["tool_results"]) == 1
        assert final_state["tool_results"][0]["status"] == "blocked"
        assert "Bloqueada" in final_state["response"] or "anti-ssrf" in final_state["response"].lower()
