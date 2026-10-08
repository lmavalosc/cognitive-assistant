# Asistente Cognitivo — Etapa 1: Núcleo Transaccional (Tronco Encefálico)

Implementación mínima ejecutable y robusta del **Tronco Encefálico** (Núcleo Transaccional) para la tesis de Asistente Cognitivo, siguiendo el principio arquitectónico **Core-to-Periphery**.

---

## 🎯 Objetivos de la Etapa 1

- [x] **FastAPI arranca** de forma limpia y modular.
- [x] **`GET /health` responde 200 OK** con metadatos de estado operativo.
- [x] **Generación de `trace_id`** en cada solicitud entrante mediante middleware asíncrono y ContextVar.
- [x] **Devolución de `trace_id` en headers HTTP** (`X-Trace-ID`).
- [x] **Inyección de `trace_id` en logs estructurados** automáticamente (`TraceIdFilter`).
- [x] **Docker Compose** orquestando API + PostgreSQL 16 + Redis 7 con healthchecks.
- [x] **Módulos y Planos Integrados**:
  - `Plano A (Infraestructura)`: Inferencia y enrutamiento LLM unificado con **LiteLLM**.
  - `Capa 2 (Recepción)`: Recepción transaccional y deliberativa (`POST /reception/deliberate`).
  - `Capa 4 (Ejecutivo Cognitivo)`: Grafo deliberativo de toma de decisiones orquestado con **LangGraph**.
  - `Capa 5 (Memoria Persistente)`: Recuerdos episódicos y preferencias del usuario gestionados con **Mem0**.
  - `Capa 8 (Efectores)`: Despachador de eventos y salida con trazabilidad universal (`trace_id`).

---

## 📂 Estructura del Proyecto

```text
cognitive-assistant/
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .env
├── .gitignore
├── docker-compose.yml
├── Dockerfile
│
├── src/
│   └── cognitive_assistant/
│       ├── __init__.py
│       ├── main.py
│       ├── app.py
│       ├── settings.py
│       │
│       ├── shared/
│       │   ├── infrastructure/
│       │   │   ├── __init__.py
│       │   │   └── llm.py                      # Plano A: Gateway LiteLLM con trazas
│       │   └── telemetry/
│       │       ├── __init__.py
│       │       ├── logging.py                  # TraceIdFilter y log estructurado
│       │       └── trace.py                    # ContextVar y TraceIDMiddleware
│       │
│       └── modules/
│           ├── c2_reception/                   # Capa 2: Recepción & Endpoints deliberativos
│           │   ├── router.py                   # /health, /reception/message, /reception/deliberate
│           │   └── schemas.py
│           ├── c4_executive/                   # Capa 4: Ejecutivo Cognitivo (LangGraph)
│           │   ├── state.py                    # CognitiveState TypedDict
│           │   └── graph.py                    # StateGraph deliberativo y ciclo cognitivo
│           ├── c5_memory/                      # Capa 5: Memoria Persistente (Mem0)
│           │   ├── router.py                   # /memory/add, /memory/search, /memory/all
│           │   ├── schemas.py
│           │   └── service.py                  # MemoryService con Mem0 y fallback local
│           └── c8_effectors/                   # Capa 8: Efectores y Despacho
│               └── dispatcher.py
│
└── tests/
    ├── test_health.py                          # Tests de salud y versión
    ├── test_trace.py                           # Tests de propagación de trace_id
    ├── test_llm_gateway.py                     # Tests de inferencia LiteLLM y fallback
    ├── test_memory_service.py                  # Tests de almacenamiento y búsqueda Mem0
    ├── test_cognitive_executive.py             # Tests del grafo deliberativo LangGraph
    └── test_cognitive_api.py                   # Tests E2E de la API cognitiva
```

---

## 🚀 Puesta en Marcha Local

### 1. Requisitos Previos

- Python 3.11+ (o 3.12)
- [uv](https://github.com/astral-sh/uv) (recomendado) o `pip` / `venv`
- Docker y Docker Compose

### 2. Configurar Entorno Virtual e Instalar Dependencias

Con **uv**:
```powershell
uv venv .venv
.\.venv\Scripts\Activate.ps1
uv pip install -e ".[dev]"
```

Con **pip** estándar:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 3. Ejecutar el Servidor en Modo Desarrollo

```powershell
uvicorn cognitive_assistant.main:app --reload --host 0.0.0.0 --port 8000
```

O directamente ejecutando el módulo:
```powershell
python src/cognitive_assistant/main.py
```

### 4. Verificar Endpoints

- **Health check:**
  ```bash
  curl -i http://localhost:8000/health
  ```
  *Respuesta esperada:*
  ```http
  HTTP/1.1 200 OK
  x-trace-id: 3c9b4e6d2a1f4b8c9d0e1f2a3b4c5d6e
  content-type: application/json

  {"status":"ok","app":"Cognitive Assistant","version":"0.1.0","trace_id":"3c9b4e6d2a1f4b8c9d0e1f2a3b4c5d6e"}
  ```

- **Ciclo Cognitivo Deliberativo (LangGraph + LiteLLM + Mem0):**
  ```bash
  curl -X POST http://localhost:8000/reception/deliberate \
    -H "Content-Type: application/json" \
    -d '{"content": "¿Cuáles son los objetivos principales?", "user_id": "moises"}'
  ```

- **Gestión de Memoria Persistente (Mem0):**
  ```bash
  curl -X POST http://localhost:8000/memory/add \
    -H "Content-Type: application/json" \
    -d '{"content": "El usuario investiga la arquitectura cognitiva de 8 capas", "user_id": "moises"}'
  ```

- **Documentación Swagger UI interactiva:**
  Visita [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Ejecución de Pruebas

Para ejecutar la suite de pruebas unitarias y de integración de trazabilidad:

```powershell
pytest -v
```

---

## 🐳 Despliegue con Docker Compose

Para levantar el entorno completo (API + PostgreSQL 16 + Redis 7):

```powershell
docker compose up --build -d
```

Verificar estado de los contenedores:
```powershell
docker compose ps
```

Ver los logs en tiempo real:
```powershell
docker compose logs -f api
```

Detener los servicios:
```powershell
docker compose down
```

---

## 🛡️ Principios del Tronco Encefálico

1. **Sin Estado Oculto:** Toda petición tiene un `trace_id` inyectado en el contexto de ejecución.
2. **Alta Resiliencia:** Servicios periféricos (PostgreSQL, Redis) cuentan con sondas de `healthcheck`.
3. **Desacoplamiento Modular:** La recepción (`c2_reception`) está separada de los efectores (`c8_effectors`) a través del despachador de eventos.
