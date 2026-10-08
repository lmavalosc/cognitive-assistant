"""Capa 5: Servicio de Memoria Persistente con mem0.

Permite memorizar preferencias del usuario, hechos episódicos y contexto semántico.
Integra mem0 con degradación elegante a almacén local para desarrollo y pruebas.
"""

import uuid
from typing import Any, Dict, List, Optional
from cognitive_assistant.settings import settings
from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id

logger = get_logger("cognitive_assistant.memory")


class MemoryService:
    """Servicio de gestión de memoria persistente basado en Mem0."""

    def __init__(self, use_mem0: bool = True) -> None:
        self.use_mem0 = use_mem0
        self._mem0_instance = None
        self._local_fallback_store: Dict[str, List[Dict[str, Any]]] = {}

        if self.use_mem0:
            self._init_mem0()

    def _init_mem0(self) -> None:
        """Intenta inicializar mem0.Memory."""
        try:
            from mem0 import Memory
            # Si hay configuración explícita o API key para embeddings
            if settings.llm_api_key:
                config = {
                    "llm": {
                        "provider": "litellm",
                        "config": {"model": settings.default_llm_model, "api_key": settings.llm_api_key},
                    }
                }
                self._mem0_instance = Memory.from_config(config)
                logger.info("mem0.Memory inicializado con configuración LiteLLM.")
            else:
                # Intentar instanciación por defecto
                self._mem0_instance = Memory()
                logger.info("mem0.Memory inicializado con configuración por defecto.")
        except Exception as exc:
            logger.warning(
                "No fue posible inicializar mem0.Memory (%s); activando almacén de memoria local.",
                exc,
            )
            self._mem0_instance = None

    async def add(
        self,
        content: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Registra un recuerdo o hecho para un usuario."""
        target_user = user_id or settings.memory_user_id
        meta = metadata or {}
        trace_id = get_trace_id()
        meta["trace_id"] = trace_id

        logger.info("Añadiendo memoria para usuario '%s': trace_id=%s", target_user, trace_id)

        if self._mem0_instance is not None:
            try:
                result = self._mem0_instance.add(
                    content,
                    user_id=target_user,
                    metadata=meta,
                )
                logger.info("Memoria añadida vía mem0 con éxito.")
                return result if isinstance(result, list) else [result]
            except Exception as exc:
                logger.warning("Fallo en mem0.add (%s); derivando a almacén local.", exc)

        # Fallback local
        item_id = str(uuid.uuid4())
        item = {
            "id": item_id,
            "memory": content,
            "user_id": target_user,
            "metadata": meta,
        }
        if target_user not in self._local_fallback_store:
            self._local_fallback_store[target_user] = []
        self._local_fallback_store[target_user].append(item)
        return [item]

    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Busca memorias relevantes para una consulta y usuario."""
        target_user = user_id or settings.memory_user_id
        trace_id = get_trace_id()

        logger.info(
            "Buscando memorias para usuario '%s', query='%s', trace_id=%s",
            target_user,
            query,
            trace_id,
        )

        if self._mem0_instance is not None:
            try:
                results = self._mem0_instance.search(
                    query=query,
                    user_id=target_user,
                    limit=limit,
                )
                if isinstance(results, list):
                    return results
                if isinstance(results, dict) and "results" in results:
                    return results["results"]
                return [results]
            except Exception as exc:
                logger.warning("Fallo en mem0.search (%s); buscando en almacén local.", exc)

        # Fallback local (búsqueda por palabras clave simple)
        user_memories = self._local_fallback_store.get(target_user, [])
        query_words = set(query.lower().split())
        matched = []
        for item in user_memories:
            text = item.get("memory", "").lower()
            overlap = sum(1 for w in query_words if w in text)
            if overlap > 0 or not query_words:
                matched.append({**item, "score": overlap / max(1, len(query_words))})

        # Si no hay match exacto pero hay memorias, retornar las más recientes
        if not matched and user_memories:
            matched = [{**item, "score": 0.1} for item in user_memories[-limit:]]

        matched.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return matched[:limit]

    async def get_all(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retorna todas las memorias asociadas a un usuario."""
        target_user = user_id or settings.memory_user_id
        if self._mem0_instance is not None:
            try:
                results = self._mem0_instance.get_all(user_id=target_user)
                if isinstance(results, list):
                    return results
                if isinstance(results, dict) and "results" in results:
                    return results["results"]
                return [results]
            except Exception as exc:
                logger.warning("Fallo en mem0.get_all (%s); leyendo de almacén local.", exc)

        return self._local_fallback_store.get(target_user, [])

    async def reset(self, user_id: Optional[str] = None) -> bool:
        """Limpia las memorias de un usuario."""
        target_user = user_id or settings.memory_user_id
        if self._mem0_instance is not None:
            try:
                self._mem0_instance.delete_all(user_id=target_user)
            except Exception as exc:
                logger.warning("Fallo en mem0.delete_all: %s", exc)

        if target_user in self._local_fallback_store:
            del self._local_fallback_store[target_user]
        return True


_memory_service_instance: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """Retorna la instancia singleton de MemoryService."""
    global _memory_service_instance
    if _memory_service_instance is None:
        _memory_service_instance = MemoryService()
    return _memory_service_instance
