"""Infraestructura compartida y abstracciones de modelos (Plano A)."""
from cognitive_assistant.shared.infrastructure.llm import LLMGateway, get_llm_gateway

__all__ = ["LLMGateway", "get_llm_gateway"]
