"""Plano A: Abstracción e inferencia de Modelos LLM con LiteLLM.

Proporciona una pasarela unificada hacia modelos locales (Ollama) y en la nube
(OpenAI, Gemini, Anthropic, etc.) con inyección de trazas (trace_id).
"""

from typing import Any, Dict, List, Optional
import litellm
from cognitive_assistant.settings import settings
from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id

logger = get_logger("cognitive_assistant.infrastructure.llm")

# Silenciar telemetría invasiva externa de litellm por defecto
litellm.telemetry = False


class LLMGateway:
    """Gateway de inferencia multimodelo basado en LiteLLM."""

    def __init__(
        self,
        default_model: Optional[str] = None,
        temperature: Optional[float] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        mock_fallback: Optional[bool] = None,
    ) -> None:
        self.default_model = default_model or settings.default_llm_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.api_key = api_key or settings.llm_api_key
        self.api_base = api_base or settings.llm_api_base
        self.mock_fallback = mock_fallback if mock_fallback is not None else settings.llm_mock_fallback

    async def acompletion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Ejecuta una compleción asíncrona unificada propagando la traza actual.
        """
        target_model = model or self.default_model
        target_temp = temperature if temperature is not None else self.temperature
        trace_id = get_trace_id()

        logger.info(
            "Invocando LLM Gateway: modelo='%s', temp=%.2f, mensajes=%d, trace_id=%s",
            target_model,
            target_temp,
            len(messages),
            trace_id,
        )

        # Si mock_fallback está activo y no hay API Key ni API Base local configurada
        if self.mock_fallback and not self.api_key and not self.api_base:
            logger.warning(
                "Sin API Key o Endpoint configurado; ejecutando modo mock_fallback para modelo '%s'",
                target_model,
            )
            user_msg = messages[-1].get("content", "") if messages else ""
            mock_content = (
                f"[Modo Cognitivo Local] Procesado con éxito mediante {target_model}. "
                f"Entrada analizada: '{user_msg[:60]}...' "
                f"(Trazabilidad: {trace_id})"
            )
            return {
                "content": mock_content,
                "model": target_model,
                "usage": {"prompt_tokens": len(user_msg.split()), "completion_tokens": 20, "total_tokens": len(user_msg.split()) + 20},
                "trace_id": trace_id,
                "provider": "mock-gateway",
            }

        call_kwargs: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": target_temp,
            **kwargs,
        }
        if self.api_key:
            call_kwargs["api_key"] = self.api_key
        if self.api_base:
            call_kwargs["api_base"] = self.api_base

        try:
            response = await litellm.acompletion(**call_kwargs)
            content = response.choices[0].message.content or ""
            usage = dict(response.usage) if hasattr(response, "usage") and response.usage else {}

            logger.info("Respuesta recibida de LLM: tokens=%s", usage)
            return {
                "content": content,
                "model": target_model,
                "usage": usage,
                "trace_id": trace_id,
                "provider": getattr(response, "model", target_model),
            }
        except Exception as exc:
            logger.error("Error en llamada a LiteLLM: %s", exc)
            if self.mock_fallback:
                logger.info("Aplicando fallback ante error de conexión externa.")
                return {
                    "content": f"[Fallback ante excepción] Error externo: {type(exc).__name__}. Traza: {trace_id}",
                    "model": target_model,
                    "usage": {},
                    "trace_id": trace_id,
                    "error": str(exc),
                    "provider": "fallback",
                }
            raise


_llm_gateway_instance: Optional[LLMGateway] = None


def get_llm_gateway() -> LLMGateway:
    """Retorna la instancia singleton de LLMGateway."""
    global _llm_gateway_instance
    if _llm_gateway_instance is None:
        _llm_gateway_instance = LLMGateway()
    return _llm_gateway_instance
