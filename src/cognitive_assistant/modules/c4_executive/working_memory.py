import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from cognitive_assistant.shared.infrastructure.redis_client import (
    redis_delete_key,
    redis_get_json,
    redis_set_json,
)

logger = logging.getLogger(__name__)


class TurnRecord(BaseModel):
    """Representación inmutable de un turno en la memoria de trabajo."""
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trace_id: str


class WorkingMemoryState(BaseModel):
    """
    Estado mental activo de una sesión conversacional (Capa 4 - Ejecutivo Cognitivo).
    Se almacena en Redis bajo la clave 'session:{session_id}:working_memory'.
    """
    session_id: str
    active_goal: Optional[str] = None
    recent_turns: List[TurnRecord] = Field(default_factory=list)
    context_summary: Optional[str] = None
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    turn_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class WorkingMemoryManager:
    """
    Gestor de la Memoria de Trabajo activa en Redis.
    Mantiene la ventana deslizante de turnos conversacionales con latencia menor a 20ms.
    """

    MAX_TURNS: int = 6
    DEFAULT_TTL: int = 86400  # 24 horas

    @classmethod
    def _format_key(cls, session_id: str, user_id: str = "default_user") -> str:
        return f"user:{user_id}:session:{session_id}:wm"

    @classmethod
    async def get_state(cls, session_id: str, user_id: str = "default_user") -> WorkingMemoryState:
        """Recupera el estado mental activo de la sesión. Si no existe, inicializa uno nuevo."""
        key = cls._format_key(session_id, user_id)
        raw_data = await redis_get_json(key)
        if not raw_data:
            raw_data = await redis_get_json(f"session:{session_id}:working_memory")

        if raw_data:
            try:
                return WorkingMemoryState.model_validate(raw_data)
            except Exception as exc:
                logger.warning("Error deserializando WorkingMemoryState para %s (user=%s): %s", session_id, user_id, exc)

        return WorkingMemoryState(session_id=session_id)

    @classmethod
    async def append_turn(
        cls,
        session_id: str,
        role: Literal["user", "assistant", "system", "tool"],
        content: str,
        trace_id: str,
        user_id: str = "default_user",
    ) -> WorkingMemoryState:
        """
        Agrega un turno conversacional aplicando la ventana deslizante (máximo MAX_TURNS).
        Actualiza el timestamp y persiste el estado en Redis.
        """
        state = await cls.get_state(session_id, user_id)
        new_turn = TurnRecord(role=role, content=content, trace_id=trace_id)

        state.recent_turns.append(new_turn)
        state.turn_count += 1
        state.last_updated = datetime.now(timezone.utc).isoformat()

        # Ventana deslizante: mantener solo los últimos MAX_TURNS turnos
        if len(state.recent_turns) > cls.MAX_TURNS:
            state.recent_turns = state.recent_turns[-cls.MAX_TURNS :]

        key = cls._format_key(session_id, user_id)
        payload = state.to_dict()
        await redis_set_json(key, payload, ttl_seconds=cls.DEFAULT_TTL)
        await redis_set_json(f"session:{session_id}:working_memory", payload, ttl_seconds=cls.DEFAULT_TTL)
        logger.debug(
            "Turno añadido a memoria de trabajo para sesión '%s' (user='%s', turnos activos=%d)",
            session_id,
            user_id,
            len(state.recent_turns),
        )
        return state

    @classmethod
    async def set_active_goal(cls, session_id: str, goal: str, user_id: str = "default_user") -> WorkingMemoryState:
        """Establece el objetivo actual en el estado mental de la sesión."""
        state = await cls.get_state(session_id, user_id)
        state.active_goal = goal
        state.last_updated = datetime.now(timezone.utc).isoformat()

        key = cls._format_key(session_id, user_id)
        payload = state.to_dict()
        await redis_set_json(key, payload, ttl_seconds=cls.DEFAULT_TTL)
        await redis_set_json(f"session:{session_id}:working_memory", payload, ttl_seconds=cls.DEFAULT_TTL)
        return state

    @classmethod
    async def set_context_summary(cls, session_id: str, summary: str, user_id: str = "default_user") -> WorkingMemoryState:
        """Establece un resumen condensado del contexto histórico acumulado."""
        state = await cls.get_state(session_id, user_id)
        state.context_summary = summary
        state.last_updated = datetime.now(timezone.utc).isoformat()

        key = cls._format_key(session_id, user_id)
        payload = state.to_dict()
        await redis_set_json(key, payload, ttl_seconds=cls.DEFAULT_TTL)
        await redis_set_json(f"session:{session_id}:working_memory", payload, ttl_seconds=cls.DEFAULT_TTL)
        return state

    @classmethod
    async def get_recent_turns(cls, session_id: str, limit: int = 6, user_id: str = "default_user") -> List[TurnRecord]:
        """Devuelve los turnos conversacionales recientes de la sesión."""
        state = await cls.get_state(session_id, user_id)
        return state.recent_turns[-limit:]

    @classmethod
    async def clear_session(cls, session_id: str, user_id: str = "default_user") -> bool:
        """Elimina el estado mental de la sesión."""
        key = cls._format_key(session_id, user_id)
        r1 = await redis_delete_key(key)
        r2 = await redis_delete_key(f"session:{session_id}:working_memory")
        return r1 or r2


