import pytest
import uuid
from cognitive_assistant.shared.infrastructure.redis_client import (
    check_redis_health,
    redis_get_json,
    redis_set_json,
    redis_delete_key,
)
from cognitive_assistant.modules.c4_executive.working_memory import WorkingMemoryManager
from cognitive_assistant.modules.c4_executive.graph import execute_cognitive_cycle


@pytest.mark.asyncio
async def test_redis_connection_and_working_memory_crud():
    """Verifica que Redis esté activo y que el gestor de memoria de trabajo realice operaciones CRUD."""
    is_healthy = await check_redis_health()
    assert is_healthy is True

    test_session = f"test-session-{uuid.uuid4().hex[:6]}"

    # 1. Estado inicial vacío
    initial_state = await WorkingMemoryManager.get_state(test_session)
    assert initial_state.session_id == test_session
    assert len(initial_state.recent_turns) == 0

    # 2. Agregar turnos
    await WorkingMemoryManager.append_turn(
        session_id=test_session,
        role="user",
        content="Hola, asistente cognitivo",
        trace_id="tr-001",
    )
    await WorkingMemoryManager.append_turn(
        session_id=test_session,
        role="assistant",
        content="Hola, ¿en qué puedo colaborar con tu investigación?",
        trace_id="tr-001",
    )

    # 3. Verificar persistencia de turnos
    state = await WorkingMemoryManager.get_state(test_session)
    assert len(state.recent_turns) == 2
    assert state.recent_turns[0].role == "user"
    assert state.recent_turns[0].content == "Hola, asistente cognitivo"
    assert state.recent_turns[1].role == "assistant"

    # 4. Establecer meta activa
    await WorkingMemoryManager.set_active_goal(test_session, "Finalizar Etapa 1 de la tesis")
    state_with_goal = await WorkingMemoryManager.get_state(test_session)
    assert state_with_goal.active_goal == "Finalizar Etapa 1 de la tesis"

    # 5. Limpiar sesión
    cleared = await WorkingMemoryManager.clear_session(test_session)
    assert cleared is True
    fresh_state = await WorkingMemoryManager.get_state(test_session)
    assert len(fresh_state.recent_turns) == 0


@pytest.mark.asyncio
async def test_working_memory_sliding_window_limit():
    """Verifica que la memoria de trabajo aplique una ventana deslizante de máximo 6 turnos."""
    test_session = f"test-window-{uuid.uuid4().hex[:6]}"

    # Insertar 10 turnos sucesivos
    for i in range(10):
        await WorkingMemoryManager.append_turn(
            session_id=test_session,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Mensaje número {i}",
            trace_id=f"tr-{i}",
        )

    state = await WorkingMemoryManager.get_state(test_session)
    assert len(state.recent_turns) == WorkingMemoryManager.MAX_TURNS
    assert state.turn_count == 10
    # El turno más antiguo en la ventana debe ser el 4 y el más reciente el 9
    assert state.recent_turns[0].content == "Mensaje número 4"
    assert state.recent_turns[-1].content == "Mensaje número 9"

    await WorkingMemoryManager.clear_session(test_session)


@pytest.mark.asyncio
async def test_working_memory_in_memory_fallback():
    """Verifica que el almacén fallback en memoria RAM funcione ante claves aisladas."""
    fallback_key = f"mock-fallback-{uuid.uuid4().hex[:6]}"
    payload = {"status": "ok", "mock": True, "value": 123}

    # Guardar y recuperar
    await redis_set_json(fallback_key, payload, ttl_seconds=60)
    retrieved = await redis_get_json(fallback_key)
    assert retrieved is not None
    assert retrieved["mock"] is True
    assert retrieved["value"] == 123

    # Eliminar
    deleted = await redis_delete_key(fallback_key)
    assert deleted is True
    assert await redis_get_json(fallback_key) is None


@pytest.mark.asyncio
async def test_conversational_continuity_scenario_1():
    """
    Validación Experimental del Escenario 1 de la Tesis:
    Verifica que en un diálogo multi-turno el Asistente recuerde el contexto inmediato de la sesión en Redis.
    """
    session_id = f"scenario-1-{uuid.uuid4().hex[:8]}"

    # Turno 1: Usuario declara información de identidad
    state_turn_1 = await execute_cognitive_cycle(
        message="Me llamo Moisés y estoy desarrollando la arquitectura de 8 capas.",
        user_id="moises_thesis",
        session_id=session_id,
    )
    assert state_turn_1["status"] == "completed"
    assert len(state_turn_1["response"]) > 0

    # Comprobar que la memoria de trabajo ahora tiene 2 turnos (user + assistant)
    wm_state_1 = await WorkingMemoryManager.get_state(session_id)
    assert len(wm_state_1.recent_turns) == 2

    # Turno 2: Usuario realiza una pregunta de seguimiento referencial
    state_turn_2 = await execute_cognitive_cycle(
        message="¿Recuerdas cuál es mi nombre y qué arquitectura estoy desarrollando?",
        user_id="moises_thesis",
        session_id=session_id,
    )
    assert state_turn_2["status"] == "completed"
    assert len(state_turn_2["dialogue_history"]) == 2  # Recibió los 2 turnos previos
    assert state_turn_2["dialogue_history"][0]["role"] == "user"
    assert "Moisés" in state_turn_2["dialogue_history"][0]["content"]

    # Comprobar que la memoria de trabajo ahora acumula 4 turnos
    wm_state_2 = await WorkingMemoryManager.get_state(session_id)
    assert len(wm_state_2.recent_turns) == 4

    await WorkingMemoryManager.clear_session(session_id)
