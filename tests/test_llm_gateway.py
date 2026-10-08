import pytest
from cognitive_assistant.shared.infrastructure.llm import LLMGateway
from cognitive_assistant.shared.telemetry.trace import get_trace_id, set_trace_id


@pytest.mark.asyncio
async def test_llm_gateway_acompletion_mock_fallback():
    """Verifica que LLMGateway funcione en modo mock_fallback con propagación de trace_id."""
    token = set_trace_id("test-llm-trace-12345")
    try:
        gateway = LLMGateway(default_model="gpt-4o-mini", mock_fallback=True)
        messages = [{"role": "user", "content": "Hola asistente cognitivo"}]

        result = await gateway.acompletion(messages=messages)

        assert "content" in result
        assert len(result["content"]) > 0
        assert result["trace_id"] == "test-llm-trace-12345"
        assert result["model"] == "gpt-4o-mini"
    finally:
        pass
