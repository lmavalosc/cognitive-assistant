"""Esquemas para la Capa 5: Memoria Persistente."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    """Representación de una memoria o hecho recuperado."""

    id: str = Field(..., description="Identificador único del registro de memoria")
    memory: str = Field(..., description="Contenido textual o hecho recordado")
    user_id: Optional[str] = Field(default=None, description="Identificador del usuario")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos contextuales")
    score: Optional[float] = Field(default=None, description="Relevancia o similitud semántica")


class AddMemoryRequest(BaseModel):
    """Petición para registrar un nuevo recuerdo o experiencia."""

    content: str = Field(..., min_length=1, description="Texto o diálogo a memorizar")
    user_id: str = Field(default="default_user", description="Usuario asociado")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")


class SearchMemoryRequest(BaseModel):
    """Petición para búsqueda de recuerdos relevantes."""

    query: str = Field(..., min_length=1, description="Consulta semántica")
    user_id: str = Field(default="default_user", description="Usuario asociado")
    limit: int = Field(default=5, ge=1, le=20, description="Límite de resultados")


class MemoryResponse(BaseModel):
    """Respuesta con lista de recuerdos."""

    memories: List[MemoryItem] = Field(default_factory=list, description="Lista de memorias")
    trace_id: str = Field(..., description="Identificador de traza")
