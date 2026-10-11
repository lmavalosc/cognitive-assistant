import pytest
from cognitive_assistant.settings import settings
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
        assert result["mock"] is True
    finally:
        pass


@pytest.mark.asyncio
async def test_llm_gateway_gemini_default_model():
    """Verifica que el modelo por defecto sea Gemini y responda correctamente en mock_fallback."""
    token = set_trace_id("test-gemini-trace-999")
    try:
        gateway = LLMGateway(mock_fallback=True)
        assert gateway.default_model == settings.default_llm_model
        assert "gemini" in gateway.default_model

        messages = [{"role": "user", "content": "¿Qué es la cognición?"}]
        result = await gateway.acompletion(messages=messages)

        assert "content" in result
        assert "gemini" in result["model"]
        assert result["trace_id"] == "test-gemini-trace-999"
        assert result["mock"] is True
    finally:
        pass


@pytest.mark.asyncio
async def test_llm_gateway_gemini_api_key_resolution(monkeypatch):
    """Verifica que gemini_api_key se resuelva automáticamente al usar modelos Gemini."""
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKeyForGeminiIntegration123")
    monkeypatch.setattr(settings, "llm_api_key", None)

    gateway = LLMGateway(default_model="gemini/gemini-2.5-flash")
    assert gateway.api_key == "AIzaSyTestKeyForGeminiIntegration123"


@pytest.mark.asyncio
async def test_llm_gateway_model_override():
    """Verifica que se pueda especificar un modelo alternativo por llamada."""
    gateway = LLMGateway(mock_fallback=True)
    result = await gateway.acompletion(
        messages=[{"role": "user", "content": "Test"}],
        model="gemini/gemini-2.5-pro",
    )
    assert result["model"] == "gemini/gemini-2.5-pro"
