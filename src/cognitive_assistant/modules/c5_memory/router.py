"""Rutas HTTP para la Capa 5: Memoria Persistente."""
from typing import List, Optional
from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from cognitive_assistant.modules.c5_memory.service import get_memory_service
from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id

router = APIRouter(prefix="/memory", tags=["Capa 5: Memoria Persistente"])
logger = get_logger("cognitive_assistant.memory.router")


class AddMemoryBody(BaseModel):
    content: str = Field(..., min_length=1, description="Contenido a recordar")
    user_id: str = Field(default="default_user", description="Identificador del usuario")
    metadata: dict = Field(default_factory=dict, description="Metadatos")


class AddMemoryResponse(BaseModel):
    status: str = "stored"
    trace_id: str
    items: List[dict]


class SearchMemoryResponse(BaseModel):
    trace_id: str
    query: str
    user_id: str
    results: List[dict]


@router.post(
    "/add",
    response_model=AddMemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Almacenar un nuevo recuerdo o preferencia",
)
async def add_memory(payload: AddMemoryBody) -> AddMemoryResponse:
    trace_id = get_trace_id()
    service = get_memory_service()
    stored = await service.add(
        content=payload.content,
        user_id=payload.user_id,
        metadata=payload.metadata,
    )
    return AddMemoryResponse(trace_id=trace_id, items=stored)


@router.get(
    "/search",
    response_model=SearchMemoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Buscar recuerdos por similitud o contexto",
)
async def search_memories(
    q: str = Query(..., min_length=1, description="Texto de búsqueda"),
    user_id: str = Query(default="default_user", description="Usuario"),
    limit: int = Query(default=5, ge=1, le=20, description="Límite"),
) -> SearchMemoryResponse:
    trace_id = get_trace_id()
    service = get_memory_service()
    results = await service.search(query=q, user_id=user_id, limit=limit)
    return SearchMemoryResponse(trace_id=trace_id, query=q, user_id=user_id, results=results)


@router.get(
    "/all",
    response_model=SearchMemoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar todas las memorias del usuario",
)
async def get_all_memories(
    user_id: str = Query(default="default_user", description="Usuario"),
) -> SearchMemoryResponse:
    trace_id = get_trace_id()
    service = get_memory_service()
    results = await service.get_all(user_id=user_id)
    return SearchMemoryResponse(trace_id=trace_id, query="*", user_id=user_id, results=results)
