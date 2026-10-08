import pytest
from cognitive_assistant.modules.c5_memory.service import MemoryService
from cognitive_assistant.shared.telemetry.trace import set_trace_id


@pytest.mark.asyncio
async def test_memory_service_add_and_search():
    """Verifica que MemoryService guarde y recupere recuerdos contextuales."""
    set_trace_id("test-mem-trace-999")
    service = MemoryService()

    # Añadir memoria
    added = await service.add(
        content="El usuario prefiere respuestas en español y con formato Markdown.",
        user_id="user_test_01",
    )
    assert len(added) > 0

    # Buscar memoria
    results = await service.search(query="español formato", user_id="user_test_01")
    assert len(results) > 0
    assert any("español" in r.get("memory", "") for r in results)

    # Listar todas
    all_mems = await service.get_all(user_id="user_test_01")
    assert len(all_mems) >= 1
