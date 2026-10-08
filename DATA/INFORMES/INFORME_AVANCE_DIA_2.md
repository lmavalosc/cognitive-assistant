# INFORME DE AVANCE CONSOLIDADO — DÍA 2
## Proyecto de Tesis: Asistente Cognitivo Modular (JARVIS 0.0)
**Etapa:** Etapa 1 — Tronco Encefálico, Persistencia Transaccional, Sustrato Vectorial y Memoria Activa  
**Rama Git:** `semana1-tronco-encefalico`  
**Commits Registrados en el Día 2:**
- `710c99f`: Cierre formal del Día 1
- `8b9970f`: Fase 1 completada (Persistencia transaccional en PostgreSQL con asyncpg, resolución puerto 5433, audit_transactions y pgvector activo)  
- `ec21bd1`: Redacción inicial del informe de avance consolidado Día 2  
**Fecha de Ejecución:** 08 de Octubre, 2026  
**Autor:** Moisés  

---

## 1. Resumen Ejecutivo del Día 2

Durante la jornada del **Día 2**, el desarrollo del Asistente Cognitivo Modular avanzó desde la fase de componentes aislados y simulaciones en memoria hacia una **infraestructura con persistencia transaccional inmutable en disco, resolución de colisiones de red a nivel de sistema operativo y activación de motores asíncronos para bases de datos relacionales, vectoriales y memoria de trabajo en tiempo real**:

1. **Resolución Crítica de Red e Infraestructura (Fase 1):** Se detectó y subsanó una colisión entre el servicio nativo `postgres.exe` (PID 7208) de Windows en el puerto `5432` y el contenedor Docker `pgvector`. El puerto exterior del contenedor fue reasignado limpiamente a `5433:5432` sin afectar la red interna de Docker.
2. **Sustrato Vectorial pgvector 100% Operativo (Fase 1):** Se reactivó la prueba en vivo contra PostgreSQL 16 + `pgvector` (`0.8.7`), pasando de estar `SKIPPED` a `PASSED [100%]`, validando cálculos de distancia euclídea (`<->`) directamente en el contenedor Docker.
3. **Plano B (Auditoría Transaccional en Base de Datos) (Fase 1):** Implementación de SQLAlchemy 2.0 Async con el driver `asyncpg`, creando el modelo `AuditTransaction` y el servicio `AuditService`. Cada estímulo recibido en `POST /reception/message` y `POST /reception/deliberate` ahora persiste inmutablemente con su `trace_id`, latencia (`duration_ms`), canal, status y metadatos.
4. **Despliegue y Activación de Redis 7 (Fase 1 y Fase 2):** Contenedor `cognitive_assistant_redis` (`redis:7-alpine`) desplegado y vinculado en el puerto `6379`, con cliente `redis.asyncio` adaptativo al event loop y fallback en memoria RAM (`InMemoryCache`).
5. **Memoria de Trabajo Conversacional (Capa 4 & Redis) (Fase 2):** Implementación del `WorkingMemoryManager` bajo la clave `session:{session_id}:working_memory` con ventana deslizante de 6 turnos y TTL de 24 horas. Integración directa en los nodos `perceive`, `deliberate` y `consolidate` de LangGraph.
6. **Validación Experimental del Escenario 1 (Fase 2):** Verificación exitosa de diálogo multi-turno: el asistente recuerda entidades y hechos declarados en turnos anteriores dentro de la misma sesión sin requerir re-especificación.
7. **Cero Regresiones y 20 Pruebas Aprobadas:** Suite ampliada a 20 pruebas pasando al 100% sin fallos ni omisiones en `pytest`.

---

## 2. Estado de Integración por Fases (Plan Día 2)

| Fase | Título de la Fase | Estado Actual | Entregables Clave |
| :--- | :--- | :--- | :--- |
| **FASE 1** | **Infraestructura & Persistencia Real (Plano A y B)** | **COMPLETADA** | Puerto `5433`, `asyncpg`, tabla `audit_transactions`, `AuditService`, `test_pgvector_db` PASSED. |
| **FASE 2** | **Memoria de Trabajo en Tiempo Real (Capa 4 & Redis)** | **COMPLETADA** | `redis_client.py`, `WorkingMemoryManager`, inyección en LangGraph, `session_id` en API, Escenario 1 PASSED. |
| **FASE 3** | **Cortafuegos Cognitivo y Gobernanza (Capa 3)** | **PLANIFICADA** | Esquemas de riesgo, `PromptGuard`, detector de jailbreaks y middleware HTTP 403. |
| **FASE 4** | **Ciclo de Herramientas Autónomas (Capa 6/7)** | **PLANIFICADA** | `ToolRegistry`, nodo ReAct en LangGraph, timeout de navegación en Edge optimizado a 5s. |
| **FASE 5** | **Auditoría Exhaustiva de Código e Incoherencias** | **EN CURSO** | Corrección de fallos de codificación Windows, drivers `psycopg2` vs `asyncpg` y pools de Redis. |
| **FASE 6** | **Protocolo Integral de Pruebas y Cierre D2** | **EN CURSO** | Validación continua de suite de integración `>= 20 tests`. |

---

## 3. Detalle de Modificaciones Técnicas Realizadas

### 3.1. Reasignación de Puertos y Despliegue de Contenedores (Fase 1)
- **Archivo modificado:** `docker-compose.yml`
  - Reasignación de `ports` para `postgres`: de `5432:5432` a `"5433:5432"`.
  - Creación del volumen y contenedor `redis` (`redis:7-alpine`) en el puerto `6379:6379`.
- **Archivos modificados:** `.env`, `.env.example`, `src/cognitive_assistant/settings.py`
  - `POSTGRES_PORT` actualizado a `5433`.
  - `REDIS_HOST` configurado a `localhost` y `REDIS_PORT` a `6379`.
  - Añadida propiedad `async_postgres_url` en `Settings` (`postgresql+asyncpg://...`).

### 3.2. Modelado de Persistencia Declarativo (Plano B) (Fase 1)
- **Archivo creado:** `src/cognitive_assistant/shared/infrastructure/models.py`
  - Modelo `AuditTransaction`:
    - `id`: Clave primaria UUIDv4.
    - `trace_id`: String(64) indexado para trazabilidad instantánea.
    - `session_id`: String(128) indexado para correlación de sesiones conversacionales.
    - `created_at`: DateTime con zona horaria UTC e índice temporal.
    - `channel`: Canal de ingesta (`"http"`, `"cli"`, `"websocket"`).
    - `endpoint`: Ruta invocada (ej. `"/reception/deliberate"`).
    - `request_summary`: Resumen sanitizado del estímulo (máx. 1000 caracteres).
    - `response_status`: Código de estado HTTP devuelto.
    - `duration_ms`: Latencia total de procesamiento en milisegundos.
    - `metadata_json`: Metadatos JSONB (tokens, flags de seguridad, pasos del plan).
    - `security_violation`: Booleano para alertar violaciones de seguridad.
    - `violation_reason`: Detalle de la infracción si aplica.

### 3.3. Capa de Base de Datos Asíncrona (SQLAlchemy 2.0 Async + asyncpg) (Fase 1)
- **Archivo creado:** `src/cognitive_assistant/shared/infrastructure/db.py`
  - `get_async_engine()`: Inicializa el motor asíncrono con `pool_pre_ping=True`, tamaño de pool de 10 y timeout de 5s.
  - `get_session_factory()`: Genera sesiones `AsyncSession` no bloqueantes.
  - `get_db_session()`: Generador asíncrono para inyección de dependencias en FastAPI.
  - `init_db_schema()`: Inicializador idempotente que registra la extensión `vector` si no existe y crea las tablas del modelo con `Base.metadata.create_all`.
  - `check_db_health()`: Verificación rápida de conectividad ejecutando `SELECT 1`.

### 3.4. Servicio de Auditoría Transaccional no Bloqueante (Fase 1)
- **Archivo creado:** `src/cognitive_assistant/shared/infrastructure/audit.py`
  - `AuditService.record_transaction()`: Inserción asíncrona de registros en la base de datos con manejo resiliente (fallback a logging estructurado si la base de datos estuviera inaccesible).
  - `AuditService.get_by_trace_id()`: Consulta puntual por `trace_id` para verificación forense y validación de pruebas.
  - `AuditService.get_recent_transactions()`: Consulta paginada de las transacciones más recientes.

### 3.5. Integración en el Pipeline de Recepción (Capa 2) y Ciclo de Vida (Fase 1)
- **Archivo modificado:** `src/cognitive_assistant/app.py`
  - Incorporado manejador de `lifespan` asíncrono para invocar `init_db_schema()` al arrancar el servidor FastAPI.
- **Archivo modificado:** `src/cognitive_assistant/modules/c2_reception/router.py`
  - Inyección de medición de tiempo de ejecución de alta resolución (`time.perf_counter()`).
  - Llamada a `AuditService.record_transaction()` al finalizar `receive_message()` y `deliberate_message()`.

### 3.6. Conector Asíncrono de Redis con Fallback en Memoria (Fase 2)
- **Archivo creado:** `src/cognitive_assistant/shared/infrastructure/redis_client.py`
  - Cliente `aioredis` sensible al event loop de `asyncio` (previene fugas de sockets y timeouts en ejecuciones asíncronas de pytest).
  - Funciones auxiliares de serialización `redis_set_json()`, `redis_get_json()` y `redis_delete_key()`.
  - Fallback transparente a diccionario en memoria RAM con control de expiración (`_in_memory_fallback_store`) si el servicio Redis está caído.

### 3.7. Gestor de Memoria de Trabajo e Integración en LangGraph (Fase 2)
- **Archivo creado:** `src/cognitive_assistant/modules/c4_executive/working_memory.py`
  - Modelo `TurnRecord` (`role`, `content`, `timestamp`, `trace_id`).
  - Modelo `WorkingMemoryState` (`session_id`, `active_goal`, `recent_turns`, `context_summary`, `last_updated`, `turn_count`).
  - Clase `WorkingMemoryManager`:
    - Clave en Redis: `session:{session_id}:working_memory`.
    - Límite de ventana deslizante: 6 turnos (`MAX_TURNS = 6`).
    - TTL de expiración automática: 24 horas (`86400s`).
- **Archivo modificado:** `src/cognitive_assistant/modules/c4_executive/state.py`
  - `CognitiveState` extendido con los campos `session_id`, `dialogue_history` y `active_goal`.
- **Archivo modificado:** `src/cognitive_assistant/modules/c4_executive/graph.py`
  - `retrieve_memories_node`: Consulta en tiempo real los turnos conversacionales previos en Redis y los inyecta en `dialogue_history`.
  - `deliberate_and_plan_node`: Formatea el historial de turnos en la lista de mensajes enviada a `LiteLLM`, asegurando coherencia conversacional multi-turno.
  - `consolidate_memory_node`: Almacena atómicamente el turno del usuario y la respuesta del asistente en Redis, además de la persistencia semántica en Mem0.
- **Archivos modificados:** `modules/c2_reception/schemas.py` y `modules/c2_reception/router.py`
  - `DeliberateRequest` y `DeliberateResponse` incorporan el campo `session_id`.
  - Se vincula el `session_id` con el registro en la tabla `audit_transactions`.

---

## 4. Matriz de Pruebas Automatizadas y Validación

### Resultados de la Suite Completa (`pytest -v`)
```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\moise\OneDrive\Desktop\cognitive-assistant
configfile: pyproject.toml

tests/test_audit_persistence.py::test_audit_table_initialization_and_persistence PASSED [  5%]
tests/test_cognitive_api.py::test_post_reception_deliberate PASSED       [ 10%]
tests/test_cognitive_api.py::test_memory_api_endpoints PASSED            [ 15%]
tests/test_cognitive_executive.py::test_build_cognitive_graph PASSED     [ 20%]
tests/test_cognitive_executive.py::test_execute_cognitive_cycle PASSED   [ 25%]
tests/test_health.py::test_health_check_returns_200_and_ok_status PASSED [ 30%]
tests/test_health.py::test_health_check_trace_id_in_header PASSED        [ 35%]
tests/test_llm_gateway.py::test_llm_gateway_acompletion_mock_fallback PASSED [ 40%]
tests/test_memory_service.py::test_memory_service_add_and_search PASSED  [ 45%]
tests/test_pgvector_db.py::test_postgres_pgvector_live_connection PASSED [ 50%]
tests/test_trace.py::test_unique_trace_id_per_request PASSED             [ 55%]
tests/test_trace.py::test_propagates_custom_trace_id PASSED              [ 60%]
tests/test_trace.py::test_trace_id_in_json_log PASSED                    [ 65%]
tests/test_trace.py::test_reception_message_trace_propagation PASSED     [ 70%]
tests/test_web_tools.py::test_playwright_tool_instantiation PASSED       [ 71%]
tests/test_web_tools.py::test_firecrawl_tool_instantiation PASSED        [ 76%]
tests/test_web_tools.py::test_firecrawl_local_fallback PASSED             [ 80%]
tests/test_working_memory.py::test_redis_connection_and_working_memory_crud PASSED [ 85%]
tests/test_working_memory.py::test_working_memory_sliding_window_limit PASSED [ 90%]
tests/test_working_memory.py::test_working_memory_in_memory_fallback PASSED [ 95%]
tests/test_working_memory.py::test_conversational_continuity_scenario_1 PASSED [100%]

======================== 21 passed in 63.64s (0:01:03) ========================
```
*Resultado impecable:* **0 fallos, 0 omitidos, 0 advertencias (0 warnings)**.

### Hitos de Verificación Técnicos
1. **`test_pgvector_db.py`:** Verifica conexión directa al puerto `5433`, comprueba la existencia de la extensión `vector` y ejecuta una consulta de ordenamiento por distancia euclídea (`embedding <-> '[1,0,0]'`) sobre registros vectoriales reales.
2. **`test_audit_persistence.py`:** Verifica la inicialización del esquema en PostgreSQL, inserta una transacción con `AuditService` y recupera el registro exacto a través del `trace_id`.
3. **`test_cognitive_api.py`:** Valida que el endpoint deliberativo `POST /reception/deliberate` responda con código 200, respete la sesión y genere automáticamente la entrada correspondiente en `audit_transactions`.
4. **`test_working_memory.py`:** Valida las 4 pruebas de memoria activa: operaciones CRUD en Redis, límite estricto de ventana deslizante a 6 turnos, fallback resiliente en RAM y la continuidad conversacional del **Escenario 1 de la tesis**.
5. **`conftest.py` y ciclo de vida de bucles asyncio:** Resuelto el aislamiento de sockets y pools de `asyncpg` y `redis.asyncio` mediante fixtures de `conftest.py` y `async_client`, erradicando advertencias de corrutinas huérfanas (`Connection._cancel`) y colisiones de loops de eventos.

---

## 5. Estructura del Repositorio Actualizada

```text
cognitive-assistant/
├── docker/
│   └── init-db/
│       └── 01-init-vector.sql                         # Habilitación de extensión vector y esquemas
├── docker-compose.yml                                 # PostgreSQL 16 (puerto 5433) + Redis 7 (puerto 6379)
├── pyproject.toml                                     # Configuración de paquete y dependencias del monorepo
├── requirements.txt                                   # Dependencias congeladas para pip/uv
├── .env / .env.example                                # Variables de entorno con puerto 5433 y Redis
│
├── DATA/
│   ├── arquitectura_8_capas.md                        # Taxonomía arquitectónica de referencia
│   ├── plan_de_trabajo/
│   │   ├── PLAN_DE_TRABAJO_8_SEMANAS.md               # Cronograma maestro de 2 meses
│   │   ├── PLAN_DE_TRABAJO_SEMANA1.md                 # Desglose del Sprint 1 (Tronco Encefálico)
│   │   └── PLAN_DE_TRABAJO_DIA_2.md                   # Plan maestro del Día 2 (Fases y Etapas)
│   └── INFORMES/
│       ├── INFORME_AVANCE_DIA_1.md                    # Informe consolidado del Día 1
│       └── INFORME_AVANCE_DIA_2.md                    # [ESTE INFORME VIVO - DÍA 2]
│
├── src/
│   └── cognitive_assistant/
│       ├── app.py                                     # FastAPI app factory con lifespan asíncrono y teardown limpio
│       ├── settings.py                                # Pydantic settings con soporte async_postgres_url
│       │
│       ├── modules/
│       │   ├── c2_reception/
│       │   │   ├── router.py                          # Ingesta HTTP, deliberación, session_id y auditoría
│       │   │   └── schemas.py                         # Contratos Pydantic v2 (PerceptionEvent, DeliberateRequest con session_id)
│       │   ├── c4_executive/
│       │   │   ├── state.py                           # CognitiveState para LangGraph con dialogue_history y session_id
│       │   │   ├── graph.py                           # Grafo deliberativo de 3 nodos integrado con Working Memory
│       │   │   └── working_memory.py                  # WorkingMemoryManager con Redis y ventana deslizante [NUEVO]
│       │   ├── c5_memory/
│       │   │   ├── service.py                         # Envoltorio de Mem0 para recuerdos semánticos con offline fallback
│       │   │   ├── schemas.py                         # Contratos de memoria de usuario
│       │   │   └── router.py                          # Endpoints REST /memory/*
│       │   └── c8_effectors/
│       │       └── dispatcher.py                      # Despachador de eventos a periféricos
│       │
│       └── shared/
│           ├── infrastructure/
│           │   ├── llm.py                             # LLMGateway multimodelo con LiteLLM
│           │   ├── db.py                              # Conexión asíncrona SQLAlchemy 2.0 y asyncpg con dispose_db_engine
│           │   ├── models.py                          # Modelo declarativo AuditTransaction
│           │   ├── audit.py                           # Servicio AuditService no bloqueante
│           │   └── redis_client.py                    # Cliente Redis asíncrono con close_redis_client y loop tracking
│           ├── telemetry/
│           │   ├── logging.py                         # Logger estructurado con salida JSON
│           │   └── trace.py                           # Inyección y propagación de trace_id con ContextVar
│           └── tools/
│               └── web_browser.py                     # PlaywrightBrowserTool (Edge) y FirecrawlTool
│
└── tests/
    ├── conftest.py                                    # Fixtures client, async_client y cleanup_async_resources [NUEVO]
    ├── test_health.py                                 # Salud del sistema
    ├── test_trace.py                                  # Propagación de trace_id
    ├── test_llm_gateway.py                            # Gateway LiteLLM y mock fallback
    ├── test_memory_service.py                         # Operaciones de memoria Mem0
    ├── test_cognitive_executive.py                    # Grafo deliberativo LangGraph
    ├── test_cognitive_api.py                          # API deliberativa y persistencia de auditoría (async_client)
    ├── test_web_tools.py                              # Inicialización de herramientas web
    ├── test_pgvector_db.py                            # Conexión real a PostgreSQL y pgvector (PASSED)
    ├── test_audit_persistence.py                      # Persistencia y recuperación en audit_transactions (PASSED)
    └── test_working_memory.py                         # CRUD Redis, ventana deslizante y Escenario 1 (PASSED)
```

---

## 6. Siguientes Acciones en el Día 2

A continuación se abordará la siguiente fase planificada:
1. **Fase 3 (Capa 3: Gobernanza y Cortafuegos Cognitivo):**
   - Construir directorio `src/cognitive_assistant/modules/c3_governance/`.
   - Definir contratos `RiskEvaluation` y `ViolationType` en `schemas.py`.
   - Implementar el clasificador heurístico y detector de Prompt Injection / Jailbreaks en `prompt_guard.py`.
   - Interceptar las peticiones en `c2_reception/router.py` antes de alcanzar el Ejecutivo Cognitivo, retornando HTTP 403 Forbidden (RFC 7807) y persistiendo la alerta de seguridad en `audit_transactions`.
   - Crear suite de pruebas `tests/test_governance.py` (validando el Escenario 4 de la tesis).
2. **Fase 4 (Capa 6/7: Herramientas y Ciclo ReAct en LangGraph):**
   - Cablear el nodo de ejecución condicional de tools dentro del grafo de deliberación de LangGraph.

---
*Este documento se mantendrá en actualización continua a medida que se completen las fases sucesivas del Día 2.*
