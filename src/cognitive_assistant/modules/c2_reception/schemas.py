from typing import Any, Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Esquema de respuesta para verificación de estado del servicio."""

    status: str = Field(default="ok", description="Estado operativo del servicio")
    service: str = Field(default="cognitive-assistant", description="Nombre del servicio")
    environment: str = Field(default="local", description="Entorno de ejecución")
    version: str = Field(default="0.1.0", description="Versión de la aplicación")


class ReceptionMessageRequest(BaseModel):
    """Esquema de entrada para recepción de eventos/mensajes transaccionales."""

    content: str = Field(..., min_length=1, max_length=8000, description="Contenido del mensaje a procesar")
    source: str = Field(default="user", description="Origen del mensaje")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos contextuales adicionales")


class ReceptionMessageResponse(BaseModel):
    """Esquema de respuesta para mensajes recibidos y despachados."""

    status: str = Field(default="accepted", description="Estado del procesamiento")
    trace_id: str = Field(..., description="Trace ID asociado al ciclo de vida del mensaje")
    dispatched: bool = Field(default=True, description="Indica si el evento fue despachado al efector")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detalles adicionales del despacho")


class DeliberateRequest(BaseModel):
    """Petición para ciclo deliberativo completo (C2 -> C5 -> C4 -> Plano A -> C8)."""

    content: str = Field(..., min_length=1, max_length=8000, description="Estímulo o mensaje de entrada a procesar")
    user_id: str = Field(default="default_user", description="Identificador del usuario")
    session_id: str = Field(default="default_session", description="Identificador de la sesión para memoria de trabajo en Redis")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos de contexto")



class DeliberateResponse(BaseModel):
    """Respuesta con deliberación cognitiva, recuerdos aplicados y plan."""

    status: str = Field(default="completed", description="Estado de la deliberación")
    trace_id: str = Field(..., description="Trace ID del ciclo cognitivo")
    session_id: str = Field(default="default_session", description="Identificador de la sesión conversacional")
    response: str = Field(..., description="Respuesta final generada por el asistente")
    plan: list[str] = Field(default_factory=list, description="Plan cognitivo formulado por LangGraph")
    context_memories: list[str] = Field(default_factory=list, description="Recuerdos recuperados desde mem0")
    dispatched: bool = Field(default=True, description="Indica si el efector C8 fue notificado")
