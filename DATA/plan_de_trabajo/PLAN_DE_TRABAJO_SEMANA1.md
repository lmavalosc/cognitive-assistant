# PLAN DE TRABAJO — SEMANA 1: Tronco Encefálico e Infraestructura (Etapa 1)

> **ACTUALIZACIÓN Y CORRECCIÓN — 08-10-2026 (vinculante, leer primero):**
> 1. **Taxonomía vigente:** 10 Capas + 2 Planos (`DATA/arquitectura_10_capas.md`, ADR 007). Las referencias "Capa 2 / Capa 8" de este documento siguen la numeración histórica v1.0; equivalencias en el documento canon (antigua C8 -> vigente C10).
> 2. **Día 05 NO cumplido:** el rate limiting Token Bucket no existe en el código (solo variables `RATE_LIMIT_*` sin consumidor — hallazgo SEC-02 de `DATA/AUDITORIA&REPARACIÓN/AUDITORIA_SEGURIDAD_2026-10-08.md`). El Hito Etapa 1 queda en estado **PARCIAL** hasta su implementación (P1 de la remediación). Nueva regla: hito superado = test en verde.
> 3. **Contrato pendiente:** `POST /api/v1/chat` nunca se implementó; la API real es `/reception/message` y `/reception/deliberate`. Queda como tarea correctiva antes de Semana 3.
> 4. **Seguridad:** este plan no incluía autenticación ni gobernanza; ambas entran por la remediación P0 (`DATA/AUDITORIA&REPARACIÓN/PROMPT_REMEDIACION_SEGURIDAD.md`), prerrequisito para cualquier herramienta autónoma.
>
> A partir de aquí, el contenido original se conserva como registro del plan tal como fue redactado.

---

Perfecto. Tomo como base el archivo **`PLAN_DE_TRABAJO_8_SEMANAS.md`** que subiste.

La **Semana 1** corresponde a:

> **Semana 1 (D01–D05): Tronco Encefálico e Infraestructura**  
> **Hito / Etapa 1:** Pipeline E/S transaccional mínimo con `trace_id` inyectado.  
> **Capas involucradas:** Plano A — Infraestructura, Capa 2 — Recepción, Capa 8 — Efectores, Plano B — Trace ID.

Te armo el plan con **6 horas efectivas diarias**, más **horas extra opcionales** si alguna tarea se atrasa.

---

# Semana 1 — Objetivo macro

Al finalizar la semana debes tener funcionando esto:

```text
1. API base levantada con FastAPI.
2. PostgreSQL y Redis conectados.
3. Endpoint POST /api/v1/chat funcionando en modo determinista / eco.
4. Cada request genera un trace_id.
5. Ese trace_id aparece en:
   - headers de respuesta
   - logs estructurados
   - registro de auditoría en base de datos
6. Rate limiting con Token Bucket sobre Redis.
7. Pruebas de integración pasando.
8. Latencia básica menor a 30 ms en la ruta simple.
9. Hito Etapa 1 superado.
```

Importante:

> En esta semana **no** conectas LLM real, RAG, agentes, IoT, memoria semántica, frontend complejo ni automatización avanzada.  
> Solo cierras el **tronco encefálico**: entrada, trazabilidad, salida básica, persistencia de auditoría y control de tasa.

---

# Jornada base recomendada

Puedes usar este horario:

```text
09:00 - 10:30  Bloque 1 — 1h 30m
10:30 - 10:45  Pausa
10:45 - 12:15  Bloque 2 — 1h 30m
12:15 - 13:00  Almuerzo / pausa larga
13:00 - 14:30  Bloque 3 — 1h 30m
14:30 - 14:45  Pausa
14:45 - 16:15  Bloque 4 — 1h 30m
```

Total: **6 horas efectivas**.

Si necesitas más, puedes agregar:

```text
16:15 - 17:15  Bloque 5 opcional — 1 hora
```

Pero solo si estás muy cerca de cerrar una tarea. No uses horas extra para abrir scope nuevo.

---

# Día 01 — Lunes  
## Infraestructura base y esqueleto del servicio

### Objetivo del día

Dejar el proyecto arrancando localmente con API, base de datos, Redis, logging básico y `trace_id` inicial.

### Entregable del día

```text
- docker-compose levanta API + PostgreSQL + Redis.
- GET /health responde 200.
- Cada request devuelve header X-Trace-ID.
- Logs estructurados incluyen trace_id.
```

---

## Bloque 1 — 09:00 a 10:30  
### Preparación del repo y entorno

Tareas:

```text
1. Crear rama de trabajo:
   git checkout -b semana1-tronco-encefalico

2. Definir estructura mínima de carpetas:

   modules/
   ├── c2_reception/
   │   ├── __init__.py
   │   ├── router.py
   │   ├── schemas.py
   │   └── rate_limiter.py
   ├── c8_effectors/
   │   ├── __init__.py
   │   └── dispatcher.py
   core/
   ├── config.py
   ├── logging.py
   ├── trace.py
   db/
   ├── session.py
   ├── models/
   │   └── audit.py
   migrations/
   tests/
   ├── test_health.py
   ├── test_trace.py
   ├── test_chat_endpoint.py
```

3. Crear `.env.example`.

Ejemplo:

```env
APP_ENV=local
API_HOST=0.0.0.0
API_PORT=8000

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=nucleo_cognitivo
POSTGRES_USER=nucleo
POSTGRES_PASSWORD=nucleo

REDIS_HOST=localhost
REDIS_PORT=6379

LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60
```

4. Agregar `.env` al `.gitignore`.

Criterio de aceptación:

```text
- Repo ordenado.
- No hay secretos commiteados.
- Estructura de carpetas lista.
```

---

## Bloque 2 — 10:45 a 12:15  
### FastAPI base y configuración

Tareas:

1. Crear aplicación FastAPI.

Archivo sugerido:

```text
main.py
```

o:

```text
app/main.py
```

Dependiendo de tu estructura. Si el plan usa `modules/`, puedes tener:

```text
modules/api.py
```

pero lo importante es exponer:

```python
app = FastAPI()
```

2. Crear `core/config.py` con Settings usando Pydantic Settings.

Ejemplo conceptual:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "nucleo_cognitivo"
    postgres_user: str = "nucleo"
    postgres_password: str = "nucleo"

    redis_host: str = "localhost"
    redis_port: int = 6379

    log_level: str = "INFO"

    rate_limit_enabled: bool = True
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60


settings = Settings()
```

3. Crear endpoint de salud.

```text
GET /health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "nucleo-cognitivo",
  "version": "0.1.0"
}
```

4. Configurar CORS mínimo para desarrollo.

Criterio de aceptación:

```text
- La API arranca.
- GET /health devuelve 200.
- Settings cargan desde .env.
```

---

## Bloque 3 — 13:00 a 14:30  
### Docker Compose: API + PostgreSQL + Redis

Tareas:

1. Crear `Dockerfile`.

Ejemplo base:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Ajusta el módulo según tu estructura real.

2. Crear `docker-compose.yml`.

Ejemplo:

```yaml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: nucleo_cognitivo
      POSTGRES_USER: nucleo
      POSTGRES_PASSWORD: nucleo
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nucleo -d nucleo_cognitivo"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

3. Crear `requirements.txt` mínimo.

Ejemplo:

```text
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
alembic
psycopg[binary]
redis
pytest
httpx
```

4. Levantar todo:

```bash
docker compose up --build
```

Criterio de aceptación:

```text
- docker compose up funciona.
- API accesible en http://localhost:8000/health.
- PostgreSQL y Redis corren.
```

---

## Bloque 4 — 14:45 a 16:15  
### Logging estructurado y trace_id inicial

Tareas:

1. Crear `core/logging.py`.

Objetivo: logs en JSON.

Ejemplo conceptual:

```python
import logging
import json
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        if hasattr(record, "trace_id"):
            log["trace_id"] = record.trace_id

        return json.dumps(log)
```

2. Crear middleware de trace.

Archivo sugerido:

```text
core/trace.py
```

Comportamiento:

```text
- Si llega header X-Trace-ID, se reutiliza.
- Si no llega, se genera UUID.
- Se guarda en contextvar.
- Se agrega a response header X-Trace-ID.
- Se inyecta en logs.
```

Ejemplo conceptual:

```python
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware

trace_id_ctx: ContextVar[str | None] = ContextVar("trace_id", default=None)


class TraceIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        trace_id_ctx.set(trace_id)

        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response
```

3. Registrar middleware en FastAPI.

```python
app.add_middleware(TraceIDMiddleware)
```

4. Probar manualmente:

```bash
curl -i http://localhost:8000/health
```

Debe devolver:

```text
X-Trace-ID: algun-uuid
```

Criterio de aceptación del día:

```text
- API arranca con Docker.
- /health responde 200.
- Cada request tiene X-Trace-ID.
- Logs incluyen trace_id.
```

---

# Día 02 — Martes  
## Capa 2: Recepción, contratos y validación

### Objetivo del día

Definir la entrada del sistema: contratos Pydantic, router de recepción y validación básica del endpoint `POST /api/v1/chat`.

### Entregable del día

```text
- POST /api/v1/chat existe.
- Valida payload.
- Devuelve errores estructurados.
- Tiene contratos PerceptionEvent y ValidatedRequest.
- Aún puede responder en modo placeholder / eco.
```

---

## Bloque 1 — 09:00 a 10:30  
### Revisión del día anterior y estabilización

Tareas:

1. Verificar que todo sigue funcionando:

```bash
docker compose up --build
curl -i http://localhost:8000/health
```

2. Corregir errores pendientes de Day 01.

3. Asegurar que `.env.example` esté completo.

4. Agregar comando rápido en README:

```bash
docker compose up --build
```

Criterio:

```text
- El sistema arranca limpio.
- No hay errores de imports.
- Health check estable.
```

---

## Bloque 2 — 10:45 a 12:15  
### Contratos Pydantic de entrada

Crear archivo:

```text
modules/c2_reception/schemas.py
```

Según tu plan, necesitas contratos base:

```text
PerceptionEvent
ValidatedRequest
```

Ejemplo conceptual:

```python
from pydantic import BaseModel, Field
from typing import Literal
from uuid import UUID


class PerceptionEvent(BaseModel):
    channel: Literal["http", "websocket", "cli", "system"] = "http"
    content: str = Field(..., min_length=1, max_length=8000)
    metadata: dict | None = None


class ValidatedRequest(BaseModel):
    trace_id: UUID
    channel: str
    content: str
    metadata: dict | None = None
```

También puedes crear un request específico para chat:

```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str | None = None
    metadata: dict | None = None
```

Y una respuesta:

```python
class ChatResponse(BaseModel):
    trace_id: UUID
    reply: str
    status: Literal["ok", "error"] = "ok"
```

Criterio:

```text
- Los modelos existen.
- Validan longitud mínima/máxima.
- Tienen tipos claros.
```

---

## Bloque 3 — 13:00 a 14:30  
### Router de recepción

Crear archivo:

```text
modules/c2_reception/router.py
```

Objetivo:

```text
POST /api/v1/chat
```

Ejemplo conceptual:

```python
from fastapi import APIRouter, Request
from uuid import UUID

from modules.c2_reception.schemas import ChatRequest, ChatResponse
from core.trace import get_trace_id

router = APIRouter(prefix="/api/v1", tags=["reception"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request):
    trace_id = get_trace_id()

    return ChatResponse(
        trace_id=trace_id,
        reply=f"Eco: {payload.message}",
        status="ok",
    )
```

Necesitarás una función auxiliar:

```text
core/trace.py
```

con:

```python
def get_trace_id() -> UUID:
    ...
```

Luego registrar router en la app:

```python
from modules.c2_reception.router import router as reception_router

app.include_router(reception_router)
```

Criterio:

```text
- POST /api/v1/chat responde 200.
- Respuesta incluye trace_id.
- Modo eco funciona.
```

---

## Bloque 4 — 14:45 a 16:15  
### Validación y errores estructurados

Tareas:

1. Agregar manejo de errores de validación.

FastAPI por defecto devuelve 422, pero puedes estandarizarlo.

Ejemplo de respuesta de error:

```json
{
  "type": "https://example.com/errors/validation",
  "title": "Solicitud inválida",
  "status": 422,
  "detail": "El campo message es obligatorio.",
  "trace_id": "..."
}
```

2. Crear exception handler global.

Archivo sugerido:

```text
core/errors.py
```

3. Asegurar que todo error incluya `trace_id`.

4. Probar payload inválido:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{}'
```

Debe devolver 422 con estructura clara.

5. Probar payload válido:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hola"}'
```

Debe devolver 200 con eco.

Criterio de aceptación del día:

```text
- POST /api/v1/chat valida entrada.
- Errores son consistentes.
- Contratos PerceptionEvent / ValidatedRequest existen.
- Router de recepción está desacoplado.
```

---

# Día 03 — Miércoles  
## Plano B: Trazabilidad, auditoría y persistencia mínima

### Objetivo del día

Convertir el `trace_id` en un hilo conductor real: logs, respuesta HTTP y tabla de auditoría.

### Entregable del día

```text
- Tabla AuditTransaction creada.
- Migración aplicada.
- Cada request POST /api/v1/chat guarda una fila.
- La fila contiene trace_id.
- Logs y DB usan el mismo trace_id.
```

---

## Bloque 1 — 09:00 a 10:30  
### Modelo SQLAlchemy de auditoría

Crear archivo:

```text
db/models/audit.py
```

Según tu plan:

```text
AuditTransaction
```

Campos mínimos:

```text
id
trace_id
created_at
channel
endpoint
payload_summary
response_status
duration_ms
metadata
```

Ejemplo conceptual:

```python
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from db.base import Base


class AuditTransaction(Base):
    __tablename__ = "audit_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    channel = Column(String(50), nullable=False)
    endpoint = Column(String(255), nullable=False)
    payload_summary = Column(Text, nullable=True)
    response_status = Column(Integer, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
```

Importante:

```text
No guardes payloads completos si pueden contener datos sensibles.
Guarda resumen, hash o campos sanitizados.
```

Criterio:

```text
- Modelo definido.
- Tiene índices por trace_id y created_at.
- No guarda secretos innecesarios.
```

---

## Bloque 2 — 10:45 a 12:15  
### Migración Alembic

Tareas:

1. Inicializar Alembic si no existe:

```bash
alembic init migrations
```

2. Configurar `sqlalchemy.url` desde settings.

3. Crear migración:

```bash
alembic revision --autogenerate -m "create audit_transactions"
```

4. Revisar manualmente la migración.

Debe crear tabla:

```text
audit_transactions
```

5. Aplicar migración:

```bash
alembic upgrade head
```

6. Verificar en PostgreSQL:

```sql
\d audit_transactions
```

Criterio:

```text
- Migración aplica sin errores.
- Tabla existe.
- Se puede revertir y reaplicar si es necesario.
```

---

## Bloque 3 — 13:00 a 14:30  
### Persistencia de auditoría por request

Tareas:

1. Crear servicio o helper:

```text
db/audit.py
```

Ejemplo conceptual:

```python
from uuid import UUID
from db.session import SessionLocal
from db.models.audit import AuditTransaction


def save_audit_transaction(
    trace_id: UUID,
    channel: str,
    endpoint: str,
    response_status: int,
    duration_ms: int | None = None,
    payload_summary: str | None = None,
    metadata: dict | None = None,
):
    with SessionLocal() as session:
        audit = AuditTransaction(
            trace_id=trace_id,
            channel=channel,
            endpoint=endpoint,
            response_status=response_status,
            duration_ms=duration_ms,
            payload_summary=payload_summary,
            metadata_=metadata or {},
        )
        session.add(audit)
        session.commit()
```

2. Integrarlo en el endpoint `/api/v1/chat`.

Flujo:

```text
inicio_time = now()
procesar request
guardar auditoría con duration_ms
retornar respuesta
```

Ejemplo conceptual:

```python
import time
from fastapi import APIRouter, Request
from modules.c2_reception.schemas import ChatRequest, ChatResponse
from core.trace import get_trace_id
from db.audit import save_audit_transaction

router = APIRouter(prefix="/api/v1", tags=["reception"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request):
    start = time.perf_counter()
    trace_id = get_trace_id()

    reply = f"Eco: {payload.message}"
    status_code = 200

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    save_audit_transaction(
        trace_id=trace_id,
        channel="http",
        endpoint="/api/v1/chat",
        response_status=status_code,
        duration_ms=elapsed_ms,
        payload_summary=payload.message[:200],
        metadata={"session_id": payload.session_id},
    )

    return ChatResponse(
        trace_id=trace_id,
        reply=reply,
        status="ok",
    )
```

Criterio:

```text
- Cada POST /chat genera una fila en audit_transactions.
- La fila tiene el mismo trace_id que la respuesta.
```

---

## Bloque 4 — 14:45 a 16:15  
### Tests de trazabilidad y auditoría

Crear tests:

```text
tests/test_trace.py
tests/test_audit.py
```

Casos mínimos:

```text
1. GET /health devuelve X-Trace-ID.
2. POST /chat devuelve trace_id en body.
3. POST /chat genera fila en audit_transactions.
4. El trace_id del response coincide con el de DB.
5. Logs contienen trace_id.
```

Ejemplo conceptual con pytest + httpx:

```python
def test_chat_creates_audit_transaction(client):
    response = client.post(
        "/api/v1/chat",
        json={"message": "hola"},
    )

    assert response.status_code == 200
    data = response.json()
    trace_id = data["trace_id"]

    # consultar DB o usar repositorio de test
    assert audit_exists(trace_id)
```

Criterio de aceptación del día:

```text
- Trazabilidad extremo a punta básica funcionando.
- Auditoría mínima persistida.
- Tests pasando.
```

---

# Día 04 — Jueves  
## Capa 8: Efectores base y endpoint chat transaccional

### Objetivo del día

Cumplir el criterio central del plan:

> **Solicitud HTTP `POST /api/v1/chat` retorna `HTTP 200` y registra la transacción en la tabla de base de datos con su `trace_id`.**

### Entregable del día

```text
- Dispatcher de efectores funcionando.
- Endpoint chat usa efector determinista.
- Respuesta estructurada.
- Auditoría correcta.
- Test e2e pasando.
```

---

## Bloque 1 — 09:00 a 10:30  
### Crear dispatcher de efectores

Crear archivo:

```text
modules/c8_effectors/dispatcher.py
```

Objetivo:

```text
Recibir una instrucción validada y devolver una acción/respuesta.
```

Ejemplo conceptual:

```python
from dataclasses import dataclass
from typing import Literal


@dataclass
class EffectorResult:
    reply: str
    status: Literal["ok", "error"] = "ok"


class DeterministicEchoEffector:
    def execute(self, content: str) -> EffectorResult:
        return EffectorResult(reply=f"Eco: {content}")


class EffectorDispatcher:
    def __init__(self):
        self.echo = DeterministicEchoEffector()

    def dispatch(self, content: str) -> EffectorResult:
        return self.echo.execute(content)
```

Para Semana 1, solo necesitas efector determinista / eco.

Criterio:

```text
- Dispatcher existe.
- No depende de LLM real.
- Es testeable unitariamente.
```

---

## Bloque 2 — 10:45 a 12:15  
### Conectar router con dispatcher

Modificar:

```text
modules/c2_reception/router.py
```

Flujo:

```text
ChatRequest
→ ValidatedRequest / PerceptionEvent
→ EffectorDispatcher
→ ChatResponse
→ AuditTransaction
```

Ejemplo conceptual:

```python
from fastapi import APIRouter
from modules.c2_reception.schemas import ChatRequest, ChatResponse
from modules.c8_effectors.dispatcher import EffectorDispatcher
from core.trace import get_trace_id
from db.audit import save_audit_transaction
import time

router = APIRouter(prefix="/api/v1", tags=["reception"])
dispatcher = EffectorDispatcher()


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    start = time.perf_counter()
    trace_id = get_trace_id()

    result = dispatcher.dispatch(payload.message)

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    save_audit_transaction(
        trace_id=trace_id,
        channel="http",
        endpoint="/api/v1/chat",
        response_status=200,
        duration_ms=elapsed_ms,
        payload_summary=payload.message[:200],
        metadata={"session_id": payload.session_id},
    )

    return ChatResponse(
        trace_id=trace_id,
        reply=result.reply,
        status=result.status,
    )
```

Criterio:

```text
- Router ya no tiene lógica dura de respuesta.
- Delega en dispatcher.
- Sigue guardando auditoría.
```

---

## Bloque 3 — 13:00 a 14:30  
### Test extremo a extremo del criterio Etapa 1

Crear o completar:

```text
tests/test_chat_endpoint.py
```

Test principal:

```python
def test_post_chat_returns_200_and_registers_trace(client):
    response = client.post(
        "/api/v1/chat",
        json={"message": "prueba etapa 1"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["reply"] == "Eco: prueba etapa 1"
    assert "trace_id" in body

    trace_id = body["trace_id"]

    assert audit_row_exists_with_trace_id(trace_id)
```

También probar:

```text
- mensaje vacío -> 422
- mensaje muy largo -> 422
- header X-Trace-ID enviado -> se reutiliza
- header X-Trace-ID no enviado -> se genera uno nuevo
```

Criterio:

```text
- El criterio oficial del plan pasa.
```

---

## Bloque 4 — 14:45 a 16:15  
### Refinamiento de respuesta y manejo de errores

Tareas:

1. Asegurar que errores también se auditen.

Ejemplo:

```text
Si payload inválido:
- response_status = 422
- se guarda auditoría si es posible
- trace_id presente
```

2. Crear respuesta de error consistente:

```json
{
  "trace_id": "...",
  "status": "error",
  "title": "Solicitud inválida",
  "detail": "..."
}
```

3. Agregar tests de error.

4. Medir latencia básica:

```bash
hey -n 100 -c 10 http://localhost:8000/api/v1/chat
```

o con k6 / locust / script propio.

Objetivo:

```text
Latencia p95 < 30 ms en ruta básica local, sin LLM externo.
```

Si rate limiting interfiere, temporalmente sube el límite para la medición o mide con límite alto.

Criterio de aceptación del día:

```text
- POST /api/v1/chat retorna 200.
- Registra transacción en DB con trace_id.
- Errores también trazables.
- Latencia básica aceptable.
```

### Horas extra opcionales

Si no alcanzaron las 6 horas, agrega:

```text
16:15 - 17:15  Bloque 5 opcional
```

Úsalo solo para:

```text
- arreglar tests e2e
- corregir persistencia de auditoría
- mejorar latencia
```

No uses este bloque para conectar LLM real.

---

# Día 05 — Viernes  
## Rate limiting, hardening y cierre del Sprint 1

### Objetivo del día

Cumplir el cierre del plan:

> **Día 05 (Viernes): Rate Limiting y Cierre del Sprint 1**  
> Configurar limitador de tasa Token Bucket sobre Redis en `modules/c2_reception/rate_limiter.py`.  
> Crear suite de pruebas de integración para ráfagas de solicitudes. Verificar código HTTP 429.  
> Ejecutar prueba cURL/Postman extremo a extremo validando latencia < 30 ms en la ruta básica.  
> **Criterio de Aceptación: Hito Etapa 1 Superado.**

### Entregable del día

```text
- Rate limiter Token Bucket en Redis.
- Requests excesivos devuelven 429.
- Suite de pruebas de ráfaga pasando.
- Latencia básica < 30 ms.
- Documentación mínima de arranque.
- Sprint 1 cerrado.
```

---

## Bloque 1 — 09:00 a 10:30  
### Implementar Token Bucket sobre Redis

Crear archivo:

```text
modules/c2_reception/rate_limiter.py
```

Comportamiento deseado:

```text
- Cada cliente/IP o clave de rate limit tiene un bucket.
- Capacidad máxima: RATE_LIMIT_REQUESTS.
- Ventana: RATE_LIMIT_WINDOW_SECONDS.
- Si excede, devuelve 429.
- Headers informativos:
  X-RateLimit-Limit
  X-RateLimit-Remaining
  X-RateLimit-Reset
```

Ejemplo conceptual simple:

```python
import time
import redis
from fastapi import HTTPException, Request
from core.config import settings

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
)


class TokenBucketRateLimiter:
    def __init__(self, capacity: int, window_seconds: int):
        self.capacity = capacity
        self.window_seconds = window_seconds

    def _key(self, identity: str) -> str:
        return f"rate_limit:{identity}"

    def allow(self, identity: str) -> tuple[bool, int, int]:
        key = self._key(identity)
        now = int(time.time())
        window_start = now - (now % self.window_seconds)
        bucket_key = f"{key}:{window_start}"

        pipe = redis_client.pipeline()
        pipe.incr(bucket_key)
        pipe.expire(bucket_key, self.window_seconds)
        result = pipe.execute()

        current = int(result[0])
        remaining = max(self.capacity - current, 0)

        if current > self.capacity:
            return False, remaining, window_start + self.window_seconds

        return True, remaining, window_start + self.window_seconds


rate_limiter = TokenBucketRateLimiter(
    capacity=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


async def enforce_rate_limit(request: Request):
    if not settings.rate_limit_enabled:
        return

    identity = request.client.host if request.client else "anonymous"
    allowed, remaining, reset_at = rate_limiter.allow(identity)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Demasiadas solicitudes. Intenta de nuevo más tarde.",
        )

    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_reset = reset_at
```

Luego usar como dependencia o middleware en `/api/v1/chat`.

Criterio:

```text
- Redis guarda contadores.
- Límite configurable por env.
- 429 cuando se excede.
```

---

## Bloque 2 — 10:45 a 12:15  
### Tests de ráfaga y 429

Crear test:

```text
tests/test_rate_limit.py
```

Casos:

```text
1. Con límite 5, las primeras 5 requests pasan con 200.
2. La request 6 devuelve 429.
3. Después de ventana, vuelve a permitir.
4. Headers de rate limit presentes.
5. Rate limit deshabilitado no bloquea.
```

Ejemplo conceptual:

```python
def test_rate_limit_blocks_after_capacity(client, monkeypatch):
    monkeypatch.setattr("core.config.settings.rate_limit_requests", 3)
    monkeypatch.setattr("core.config.settings.rate_limit_enabled", True)

    for _ in range(3):
        r = client.post("/api/v1/chat", json={"message": "hola"})
        assert r.status_code == 200

    r = client.post("/api/v1/chat", json={"message": "hola"})
    assert r.status_code == 429
```

Importante:

```text
Usa un Redis de test aislado o limpia claves antes/después.
No dependas de estado global entre tests.
```

Criterio:

```text
- Suite de ráfaga pasa.
- 429 verificado.
```

---

## Bloque 3 — 13:00 a 14:30  
### Prueba e2e y latencia < 30 ms

Tareas:

1. Levantar stack limpio:

```bash
docker compose down -v
docker compose up --build
```

2. Aplicar migraciones si es necesario:

```bash
alembic upgrade head
```

3. Ejecutar prueba manual:

```bash
curl -i -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"cierre sprint 1"}'
```

Verificar:

```text
HTTP/1.1 200 OK
X-Trace-ID: ...
```

Body:

```json
{
  "trace_id": "...",
  "reply": "Eco: cierre sprint 1",
  "status": "ok"
}
```

4. Verificar auditoría:

```sql
SELECT trace_id, endpoint, response_status, duration_ms
FROM audit_transactions
ORDER BY created_at DESC
LIMIT 5;
```

5. Medir latencia.

Opción simple con Python:

```python
import httpx
import statistics
import time

url = "http://localhost:8000/api/v1/chat"
latencies = []

for i in range(100):
    start = time.perf_counter()
    r = httpx.post(url, json={"message": f"msg {i}"})
    elapsed = (time.perf_counter() - start) * 1000
    latencies.append(elapsed)
    assert r.status_code in (200, 429)

print("p50:", statistics.median(latencies))
print("p95:", sorted(latencies)[int(len(latencies) * 0.95)])
```

Objetivo:

```text
p95 < 30 ms en ruta básica local.
```

Si rate limiting interfiere, temporalmente sube el límite para la medición o mide con límite alto.

Criterio:

```text
- e2e funciona.
- auditoría se registra.
- latencia básica cumple objetivo.
```

---

## Bloque 4 — 14:45 a 16:15  
### Documentación, checklist y cierre de Sprint 1

Actualizar README:

```text
README.md
```

Debe incluir:

```text
1. Requisitos.
2. Variables de entorno.
3. Comando docker compose up.
4. Comando alembic upgrade head.
5. Endpoint /health.
6. Endpoint POST /api/v1/chat.
7. Cómo correr tests.
8. Cómo verificar trace_id.
9. Cómo verificar auditoría.
10. Configuración de rate limit.
```

Crear checklist:

```text
docs/sprints/semana1-checklist.md
```

Contenido:

```md
# Checklist Semana 1 — Tronco Encefálico

- [ ] Docker compose levanta API, PostgreSQL y Redis.
- [ ] GET /health responde 200.
- [ ] POST /api/v1/chat responde 200.
- [ ] Cada request tiene X-Trace-ID.
- [ ] Logs estructurados incluyen trace_id.
- [ ] AuditTransaction se guarda en PostgreSQL.
- [ ] trace_id coincide entre response, logs y DB.
- [ ] Rate limiter Token Bucket usa Redis.
- [ ] Ráfaga excesiva devuelve 429.
- [ ] Tests unitarios e integración pasan.
- [ ] Latencia p95 < 30 ms en ruta básica.
- [ ] README actualizado.
- [ ] Hito Etapa 1 superado.
```

Ejecutar suite final:

```bash
pytest -q
```

Hacer commit:

```bash
git add .
git commit -m "feat(semana1): cierre tronco encefalico con trace, auditoria, chat eco y rate limiting"
```

Tag opcional:

```bash
git tag sprint1-etapa1-completada
```

Criterio final del día:

```text
Hito Etapa 1 Superado.
```

### Horas extra opcionales

Si el cierre se atrasa:

```text
16:15 - 17:15  Bloque 5 opcional
17:15 - 18:15  Bloque 6 opcional solo si es crítico
```

Úsalos para:

```text
- arreglar tests rotos
- corregir rate limiting
- mejorar documentación
- validar latencia
```

No los uses para empezar Semana 2.

---

# Resumen visual de la semana

| Día | Foco principal | Entregable clave |
|---|---|---|
| Día 01 | Infraestructura | API + DB + Redis + health + trace_id |
| Día 02 | Capa 2 Recepción | Contratos + POST /chat validado |
| Día 03 | Plano B Trazabilidad | AuditTransaction + migración + tests |
| Día 04 | Capa 8 Efectores | Dispatcher eco + e2e + auditoría correcta |
| Día 05 | Rate limiting y cierre | Token Bucket + 429 + latencia + Sprint 1 cerrado |

---

# Definition of Done de la Semana 1

La Semana 1 está terminada solo si cumples todo esto:

```text
[ ] El proyecto arranca con un solo comando o documento claro.
[ ] PostgreSQL y Redis están integrados.
[ ] GET /health devuelve 200.
[ ] POST /api/v1/chat devuelve 200 con payload válido.
[ ] POST /api/v1/chat devuelve 422 con payload inválido.
[ ] Cada request tiene trace_id.
[ ] trace_id se devuelve en header X-Trace-ID.
[ ] trace_id aparece en logs estructurados.
[ ] trace_id se guarda en audit_transactions.
[ ] La tabla audit_transactions existe vía migración.
[ ] Hay tests de health.
[ ] Hay tests de chat.
[ ] Hay tests de trazabilidad.
[ ] Hay tests de auditoría.
[ ] Hay rate limiting Token Bucket sobre Redis.
[ ] Las requests excesivas devuelven 429.
[ ] Hay tests de ráfaga.
[ ] Latencia p95 de ruta básica < 30 ms en entorno local.
[ ] README actualizado.
[ ] Checklist Sprint 1 completo.
[ ] Hito Etapa 1 superado.
```

---

# Archivos mínimos que deberías tener al final de la semana

```text
.env.example
docker-compose.yml
Dockerfile
requirements.txt
README.md

core/
  config.py
  logging.py
  trace.py
  errors.py

db/
  base.py
  session.py
  audit.py
  models/
    audit.py

migrations/
  versions/
    xxxx_create_audit_transactions.py

modules/
  c2_reception/
    router.py
    schemas.py
    rate_limiter.py
  c8_effectors/
    dispatcher.py

tests/
  test_health.py
  test_trace.py
  test_chat_endpoint.py
  test_audit.py
  test_rate_limit.py

docs/
  sprints/
    semana1-checklist.md
```

---

# Reglas para no desviarte esta semana

No hagas esto todavía:

```text
- No conectar OpenAI / Anthropic / Ollama real.
- No implementar memoria de trabajo en Redis para conversación larga.
- No hacer RAG.
- No hacer pgvector.
- No hacer agentes especializados.
- No hacer planner.
- No hacer guardrails complejos.
- No hacer IoT mocks.
- No hacer frontend.
- No hacer VoIP / Telegram / WhatsApp.
- No hacer Docker runner para herramientas.
```

Solo esto:

```text
Infraestructura + recepción + trace + auditoría + efector eco + rate limit.
```

---

# Si trabajas 6 horas diarias, ruta recomendada

```text
Lunes:  6h — infraestructura
Martes: 6h — recepción y contratos
Miércoles: 6h — trazabilidad y auditoría
Jueves: 6h + 1h opcional — efectores y e2e
Viernes: 6h + 1-2h opcional — rate limit y cierre
```

Total base:

```text
30 horas
```

Total con horas extra:

```text
32 a 33 horas
```

---

# Mini plan de contingencia

Si el lunes te atrasas:

```text
Mueve logging avanzado a miércoles.
Lo esencial del lunes es: API, health, Docker, trace_id básico.
```

Si el martes te atrasas:

```text
Deja errores estructurados simples para jueves.
Lo esencial es: POST /chat valida y responde eco.
```

Si el miércoles te atrasas:

```text
Prioriza tabla AuditTransaction y migración.
Tests de auditoría pueden extenderse a jueves.
```

Si el jueves te atrasas:

```text
Usa bloque extra de 1h.
No pases viernes sin e2e funcionando.
```

Si el viernes te atrasas:

```text
Usa 1-2h extra.
Si aún no alcanza, reduce scope de tests de ráfaga a 3 casos mínimos:
- permite bajo límite
- bloquea sobre límite
- devuelve 429
```

---

# Criterio final de éxito de la Semana 1

Debes poder ejecutar esta demo:

```bash
docker compose up --build
alembic upgrade head
pytest -q
```

Y luego:

```bash
curl -i -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Semana 1 completada"}'
```

Resultado esperado:

```text
HTTP 200
X-Trace-ID: uuid
body con trace_id y reply eco
fila en audit_transactions con ese trace_id
logs con ese trace_id
rate limiting funcionando
latencia básica aceptable
```

Si eso ocurre:

> **Semana 1 cerrada. Etapa 1 superada. Puedes entrar a Semana 2: Memoria de Trabajo y Conexión LLM.**