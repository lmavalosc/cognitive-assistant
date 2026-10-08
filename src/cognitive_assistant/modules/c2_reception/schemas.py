from typing import Any, Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Esquema de respuesta para verificación de estado del servicio."""

    status: str = Field(default="ok", description="Estado operativo del servicio")
    app: str = Field(..., description="Nombre del servicio")
    version: str = Field(..., description="Versión de la aplicación")
    trace_id: str = Field(..., description="Identificador único de trazabilidad de la solicitud")


class ReceptionMessageRequest(BaseModel):
    """Esquema de entrada para recepción de eventos/mensajes transaccionales."""

    content: str = Field(..., min_length=1, description="Contenido del mensaje a procesar")
    source: str = Field(default="user", description="Origen del mensaje (ej: user, system, webhook)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos contextuales adicionales")


class ReceptionMessageResponse(BaseModel):
    """Esquema de respuesta para mensajes recibidos y despachados."""

    status: str = Field(default="accepted", description="Estado del procesamiento")
    trace_id: str = Field(..., description="Trace ID asociado al ciclo de vida del mensaje")
    dispatched: bool = Field(default=True, description="Indica si el evento fue despachado al efector")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detalles adicionales del despacho")
