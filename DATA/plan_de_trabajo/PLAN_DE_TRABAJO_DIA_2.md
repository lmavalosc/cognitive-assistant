# PLAN DE TRABAJO MAESTRO — DÍA 2
## Proyecto de Tesis: Asistente Cognitivo Modular (JARVIS 0.0)
**Documento Técnico:** `TR-COG-2026-PLAN-D2` / `DATA/plan_de_trabajo/PLAN_DE_TRABAJO_DIA_2.md`  
**Metodología:** *Core-to-Periphery* + Monolito Modular Hexagonal  
**Rama Git:** `semana1-tronco-encefalico` (Cierre Día 1: Commit `710c99f`)  
**Fecha de Elaboración:** 08 de Octubre, 2026
**Autor:** Moisés

> **ACTUALIZACIÓN Y CORRECCIÓN — 08-10-2026 (vinculante, leer primero):**
> 1. **Taxonomía:** arquitectura vigente de **10 Capas + 2 Planos** (`DATA/arquitectura_10_capas.md`, ADR 007). En este documento: "Capa 4" -> vigentes C4 (memoria de trabajo) + C5 (ejecutivo); "Capa 6/7" -> vigentes C7 (agentes) + C8 (sandbox).
> 2. **Puerta de seguridad:** la **FASE 4 queda BLOQUEADA** hasta completar la remediación P0 (`DATA/AUDITORIA&REPARACIÓN/AUDITORIA_SEGURIDAD_2026-10-08.md`, `DATA/AUDITORIA&REPARACIÓN/PROMPT_REMEDIACION_SEGURIDAD.md`): Capa 3 (PromptGuard + 403 RFC 7807), autenticación por API key con user_id derivado, y validador anti-SSRF en las herramientas web. Razón: sin C3, cablear herramientas encadena prompt injection -> envenenamiento de memoria -> SSRF.
> 3. **Correcciones de la Fase 3/4 ya detectadas en auditoría:** `max_length=8000` faltante en contratos; `user_id`/`session_id` autodeclarados (SEC-05) — la Etapa 3.3 y las claves Redis de la 2.2 deberán incorporar namespace por usuario; timeout de Playwright en 20000 ms (Etapa 4.3 sigue pendiente; ahora forma parte de la Parte C de la remediación, no de la Fase 4).
> 4. **La Fase 3 absorbió los P0/P1** del prompt de remediación (especificados allí como Partes A-D). Este plan queda como especificación funcional; la especificación operativa de implementación es `DATA/AUDITORIA&REPARACIÓN/PROMPT_REMEDIACION_SEGURIDAD.md`.
>
> A partir de aquí, el contenido original se conserva.

---

## 1. Declaración de Cierre del Día 1 e Inicio del Día 2

### Cierre Formal del Día 1
El **Día 1** ha sido formalmente cerrado, validado y registrado en el control de versiones:
- **Commit de Cierre:** `710c99f` — `feat(dia-1): cierre formal dia 1 - integracion de tronco encefalico, litellm, langgraph, mem0, pgvector y herramientas web`.
- **Archivos Commiteados:** 30 archivos (`src/cognitive_assistant/`, `tests/`, `docker/`, `DATA/INFORMES/INFORME_AVANCE_DIA_1.md`, configuraciones).
- **Estado de Pruebas:** 15 pruebas pasando exitosamente, 1 prueba skipped (`pytest -v` verificado en 185s).
- **Entorno:** Python 3.14.7 sobre entorno virtual `.venv` con dependencias base (`litellm`, `langgraph`, `mem0ai`, `firecrawl-py`, `playwright`, `asyncpg`, `pgvector`).

### Misión y Alcance del Día 2
El **Día 2** tiene como objetivo llevar al Asistente Cognitivo desde un estado de componentes acoplados con simulaciones/mocks hacia un **sistema neuro-funcional coordinado, blindado y persistente en tiempo real**, estructurado rigurosamente en **Fases** y **Etapas** exhaustivas.

---

## 2. Estructura del Plan: Fases y Etapas de Desarrollo

```mermaid
flowchart TD
    subgraph FASE1 ["FASE 1: INFRAESTRUCTURA & PERSISTENCIA REAL (PLANO A & B)"]
        E11["Etapa 1.1: Resolución Colisión Puertos PG (5433:5432)"] --> E12["Etapa 1.2: Modelos SQLAlchemy 2.0 Async (AuditTransaction)"]
        E12 --> E13["Etapa 1.3: Servicio Asíncrono AuditService y pgvector"]
    end

    subgraph FASE2 ["FASE 2: MEMORIA DE TRABAJO EN TIEMPO REAL (CAPA 4 & REDIS)"]
        E21["Etapa 2.1: Conector Asíncrono Redis 7 con Fallback"] --> E22["Etapa 2.2: WorkingMemoryManager session:{id} (< 20ms)"]
        E22 --> E23["Etapa 2.3: Inyección de Working Memory en LangGraph"]
    end

    subgraph FASE3 ["FASE 3: CORTAFUEGOS COGNITIVO & GOBERNANZA (CAPA 3)"]
        E31["Etapa 3.1: Contratos y Esquemas de Riesgo (RiskEvaluation)"] --> E32["Etapa 3.2: PromptGuard Heurístico & Anti-Jailbreak"]
        E32 --> E33["Etapa 3.3: Interceptor Perimétrico en C2 (HTTP 403 / RFC 7807)"]
    end

    subgraph FASE4 ["FASE 4: CICLO DE HERRAMIENTAS AUTÓNOMAS (CAPA 6/7 & LANGGRAPH)"]
        E41["Etapa 4.1: Registro Tipado de Herramientas (ToolRegistry)"] --> E42["Etapa 4.2: Nodo ReAct en Grafo Deliberativo (tools_node)"]
        E42 --> E43["Etapa 4.3: Optimización de Timeouts en Playwright Edge"]
    end

    FASE1 --> FASE2
    FASE2 --> FASE3
    FASE3 --> FASE4
```

---

### FASE 1: Infraestructura de Persistencia Real y Auditoría Transaccional (Plano A y Plano B)

#### Justificación y Explicación de la Fase:
En el Día 1, la base de datos PostgreSQL con `pgvector` fue inicializada en Docker, pero se detectó una colisión de puertos con un proceso nativo `postgres.exe` (PID 7208) en Windows en el puerto `5432`. Asimismo, la auditoría de peticiones operó puramente en memoria y logs JSON. La Fase 1 dota al sistema de persistencia inmutable en disco mediante SQLAlchemy 2.0 Async y `asyncpg`, eliminando dependencias de `psycopg2` y resolviendo la conectividad real con `pgvector`.

---

#### Etapa 1.1: Remediación de Red y Configuración del Puerto de Base de Datos
- **Explicación:**
  Para evitar colisiones entre el PostgreSQL local de Windows (puerto 5432) y el contenedor de Docker `cognitive_assistant_postgres`, se remapea el puerto exterior del contenedor al `5433:5432`. De esta manera, Docker sigue ejecutando PostgreSQL internamente en su puerto estándar 5432, pero el host y la aplicación de desarrollo se comunican limpiamente por el puerto `5433` sin conflicto ni reseteo de sockets.
- **Lo que se va a modificar:**
  - `docker-compose.yml`: Modificar el mapeo de puertos del servicio `postgres` de `5432:5432` a `"5433:5432"`.
  - `.env` y `.env.example`: Actualizar `POSTGRES_PORT=5433`.
  - `src/cognitive_assistant/settings.py`: Actualizar el valor por defecto de `postgres_port: int = 5433`.
- **Criterios de Aceptación:**
  - `docker compose up -d postgres` levanta sin alertas de puerto ocupado.
  - Conexión vía socket TCP al puerto `5433` responde exitosamente en < 5 ms.

---

#### Etapa 1.2: Modelado Asíncrono de Auditoría Transaccional (`AuditTransaction`)
- **Explicación:**
  Cada interacción que ingresa al Asistente Cognitivo debe quedar registrada para cumplir con el **Plano B (Trazabilidad Universal)**. Se define un modelo declarativo con SQLAlchemy 2.0 que captura el `trace_id`, la latencia exacta de procesamiento, el canal de entrada, el estado de respuesta HTTP, un resumen sanitizado del estímulo y metadatos JSON con los identificadores de modelos utilizados.
- **Lo que se va a modificar o crear:**
  - Crear `src/cognitive_assistant/shared/infrastructure/db.py`:
    - Inicialización de `create_async_engine` con URL `postgresql+asyncpg://nucleo:nucleo@localhost:5433/nucleo_cognitivo`.
    - Configuración de `async_sessionmaker(expire_on_commit=False)`.
    - Función generadora de sesiones `async def get_db_session()`.
    - Función de auto-creación asíncrona de tablas `async def init_db_schema()`.
  - Crear `src/cognitive_assistant/shared/infrastructure/models.py`:
    - Modelo `AuditTransaction(Base)` con tabla `audit_transactions`.
    - Campos: `id` (UUID PK), `trace_id` (UUID Index), `session_id` (String Index), `created_at` (DateTime UTC Index), `channel` (String), `endpoint` (String), `request_summary` (Text), `response_status` (Integer), `duration_ms` (Float), `metadata_json` (JSONB).
- **Criterios de Aceptación:**
  - La tabla `audit_transactions` se crea automáticamente con sus índices correspondientes en PostgreSQL.

---

#### Etapa 1.3: Servicio de Auditoría Asíncrona y Prueba Real de pgvector
- **Explicación:**
  Se construye `AuditService` para persistir los registros sin bloquear el hilo principal de FastAPI. Se actualiza la prueba `tests/test_pgvector_db.py` para usar `asyncpg` apuntando al puerto `5433`, verificando inserciones vectoriales reales y similitud por distancia Euclídea/Coseno.
- **Lo que se va a modificar o crear:**
  - Crear `src/cognitive_assistant/shared/infrastructure/audit.py`:
    - Clase `AuditService` con método `record_transaction(...)`.
    - Manejo resiliente: si la base de datos experimenta un fallo temporal, el registro se vuelca a logs JSON sin interrumpir la respuesta al usuario.
  - Modificar `tests/test_pgvector_db.py`:
    - Migrar de `psycopg2` a `asyncpg` conectando a `localhost:5433`.
    - Ejecutar prueba real de creación de tabla con `vector(3)` y cálculo de distancia `<->`.
- **Criterios de Aceptación:**
  - `tests/test_pgvector_db.py` pasa con resultado `PASSED` (0 tests skipped).
  - Toda petición procesada por la API inserta una fila en `audit_transactions`.

---

### FASE 2: Sustrato de Memoria de Trabajo en Tiempo Real (Capa 4 & Redis)

#### Justificación y Explicación de la Fase:
En el Día 1, el grafo cognitivo operó de forma transaccional stateless: cada petición se procesaba de manera aislada. Para cumplir con el **Escenario Experimental 1** de la tesis, el Asistente debe mantener un **estado mental activo (Working Memory)** en Redis bajo la clave `session:{session_id}:working_memory`, recordando turnos conversacionales previos, objetivos activos y restricciones con tiempos de respuesta menores a 20 ms.

---

#### Etapa 2.1: Infraestructura de Conexión Asíncrona a Redis 7
- **Explicación:**
  Se configura el cliente asíncrono oficial de Redis para Python con pool de conexiones, timeout de socket de 500 ms y reintentos automáticos. Para garantizar la política de degradación elegante, se implementa un mecanismo de fallback transparente en memoria RAM (`InMemoryCache`) en caso de que el servicio Redis no esté disponible.
- **Lo que se va a modificar o crear:**
  - Modificar `docker-compose.yml`: Asegurar servicio `redis` con imagen `redis:7-alpine` en puerto `6379:6379`.
  - Crear `src/cognitive_assistant/shared/infrastructure/redis_client.py`:
    - Singleton `get_redis_client() -> redis.asyncio.Redis`.
    - Wrapper con control de excepciones y verificación de salud `async def check_redis_health() -> bool`.
- **Criterios de Aceptación:**
  - Conexión a Redis 7 verificada con `PING -> PONG`.
  - Si el contenedor Redis está detenido, el cliente detecta el fallo sin provocar excepciones no controladas.

---

#### Etapa 2.2: Diseñar y Construir el Gestor de Memoria de Trabajo (`WorkingMemoryManager`)
- **Explicación:**
  La memoria de trabajo almacena la ventana deslizante de los últimos 6 turnos conversacionales (`user` y `assistant`), el objetivo activo (`active_goal`) y las notas de contexto. Cada sesión tiene asignado un TTL de 24 horas en Redis para optimizar el uso de recursos de memoria.
- **Lo que se va a modificar o crear:**
  - Crear `src/cognitive_assistant/modules/c4_executive/working_memory.py`:
    - Modelo `TurnRecord`: `role: str`, `content: str`, `timestamp: str`, `trace_id: str`.
    - Modelo `WorkingMemoryState`: `session_id: str`, `active_goal: str | None`, `recent_turns: list[TurnRecord]`, `last_updated: str`.
    - Clase `WorkingMemoryManager`:
      - `async def get_state(session_id: str) -> WorkingMemoryState`
      - `async def append_turn(session_id: str, role: str, content: str, trace_id: str) -> None`
      - `async def set_goal(session_id: str, goal: str) -> None`
      - `async def clear(session_id: str) -> None`
- **Criterios de Aceptación:**
  - Lectura y escritura en Redis en menos de 15 ms.
  - Preservación exacta de turnos históricos en orden cronológico.

---

#### Etapa 2.3: Integración de la Memoria de Trabajo en LangGraph
- **Explicación:**
  Se conecta `WorkingMemoryManager` dentro del grafo deliberativo de Capa 4:
  1. En el nodo `perceive`: Se extraen los turnos recientes de la sesión y se inyectan en el estado `CognitiveState.dialogue_history`.
  2. En el nodo `deliberate`: El LLM recibe en su prompt tanto la memoria episódica/semántica de Mem0 como el historial inmediato de Redis.
  3. En el nodo `consolidate`: Se añade el nuevo turno del usuario y la respuesta del asistente a la memoria de trabajo de Redis.
- **Lo que se va a modificar:**
  - Modificar `src/cognitive_assistant/modules/c4_executive/state.py`: Añadir campo `dialogue_history: list[dict] = Field(default_factory=list)`.
  - Modificar `src/cognitive_assistant/modules/c4_executive/graph.py`: Actualizar las funciones de nodo `perceive_node` y `consolidate_node` para sincronizar con `WorkingMemoryManager`.
- **Criterios de Aceptación:**
  - Diálogo en dos pasos: Turno 1 ("Mi nombre es Moisés"), Turno 2 ("¿Cómo me llamo?"). El sistema responde reconociendo el nombre sin reespecificación.

---

### FASE 3: Cortafuegos Cognitivo y Gobernanza Perimétrica (Capa 3)

#### Justificación y Explicación de la Fase:
El Asistente Cognitivo requiere protección perimétrica antes de que los estímulos externos lleguen al Ejecutivo Cognitivo o consuman inferencia en el LLM. La **Capa 3 (Gobernanza y Control de Riesgos)** actúa como cortafuegos heurístico y de políticas, neutralizando ataques de Prompt Injection, intentos de jailbreak y fugas de contexto perimétrico, respondiendo con códigos de error estandarizados RFC 7807 (HTTP 403 / 422).

---

#### Etapa 3.1: Definición de Contratos y Taxonomía de Riesgo
- **Explicación:**
  Se definen los tipos de violación de seguridad y el modelo de evaluación de riesgo que clasifica cada estímulo antes de su procesamiento cognitivo.
- **Lo que se va a crear:**
  - Crear `src/cognitive_assistant/modules/c3_governance/schemas.py`:
    - Enumeración `ViolationType`: `PROMPT_INJECTION`, `JAILBREAK_ATTEMPT`, `SYSTEM_PROMPT_LEAK`, `PAYLOAD_OVERSIZED`, `INVALID_CONTROL_CHARS`, `NONE`.
    - Modelo `RiskEvaluation`:
      - `risk_score: float` (0.0 a 1.0).
      - `allowed: bool`.
      - `violation_type: ViolationType`.
      - `reason: str | None`.
      - `sanitized_content: str`.
      - `trace_id: str`.
- **Criterios de Aceptación:**
  - Modelos tipados y validados con Pydantic v2.

---

#### Etapa 3.2: Motor de Detección Heurística (`PromptGuard`) y Sanitización
- **Explicación:**
  Se construye un motor de reglas determinista de alta velocidad (< 5 ms) que analiza patrones adversarios conocidos:
  - Firmas de anulación: `"ignore previous instructions"`, `"ignore all prompts"`, `"bypass system"`.
  - Firmas de jailbreak: `"DAN mode"`, `"developer mode enabled"`, `"pretend you have no limits"`.
  - Firmas de exfiltración: `"print system prompt"`, `"show environment variables"`, `"dump api keys"`.
  - Sanitizador: remoción de caracteres de control nulos (`\x00`), normalización NFKC de Unicode y límite estricto de longitud (8,000 caracteres).
- **Lo que se va a crear:**
  - Crear `src/cognitive_assistant/modules/c3_governance/prompt_guard.py`: Clase `PromptGuard` con métodos `evaluate_risk(content: str) -> RiskEvaluation`.
  - Crear `src/cognitive_assistant/modules/c3_governance/sanitizer.py`: Clase `InputSanitizer` con método `sanitize(content: str) -> str`.
  - Crear `src/cognitive_assistant/modules/c3_governance/service.py`: Clase `GovernanceService` que coordina sanitización, evaluación de riesgo y auditoría de seguridad.
- **Criterios de Aceptación:**
  - Prompts benignos obtienen `risk_score = 0.0` y `allowed = True`.
  - Prompts maliciosos obtienen `risk_score >= 0.7` y `allowed = False`.

---

#### Etapa 3.3: Interceptor Perimétrico en Capa 2 (Recepción)
- **Explicación:**
  Se interceptan las peticiones en `src/cognitive_assistant/modules/c2_reception/router.py` antes de llamar al Ejecutivo Cognitivo:
  1. Si `RiskEvaluation.allowed == False`:
     - Se registra inmediatamente la violación en `AuditService` con estado HTTP 403 y metadatos de riesgo.
     - Se retorna un error estructurado RFC 7807 (`ProblemDetails`) con código 403 y mensaje `"Infracción de seguridad cognitiva: Intento de Prompt Injection detectado"`.
     - Se corta el flujo inmediatamente sin invocar a Capa 4 ni consumir tokens de LLM.
  2. Si `RiskEvaluation.allowed == True`:
     - El contenido sanitizado se envía a Capa 4.
- **Lo que se va a modificar:**
  - Modificar `src/cognitive_assistant/modules/c2_reception/router.py`: Inyectar `GovernanceService` en los endpoints `POST /api/v1/chat` y `POST /reception/deliberate`.
- **Criterios de Aceptación:**
  - Pruebas cURL y tests automatizados verifican bloqueo estricto con HTTP 403 ante ataques adversarios sintéticos.

---

### FASE 4: Activación del Ciclo de Herramientas Autónomas (Capa 6/7 y LangGraph)

#### Justificación y Explicación de la Fase:
En el Día 1 se crearon las herramientas periféricas `PlaywrightBrowserTool` y `FirecrawlTool`, pero el grafo de LangGraph no contaba con un nodo de decisión y ejecución de herramientas. La Fase 4 conecta estas capacidades en un ciclo **ReAct (Reasoning + Acting)** en LangGraph, permitiendo que el Asistente decida cuándo requiere navegar por la web y extraiga contenido de forma segura.

---

#### Etapa 4.1: Catálogo y Registro Unificado de Herramientas (`ToolRegistry`)
- **Explicación:**
  Se crea una interfaz estandarizada para registrar herramientas ejecutables con esquemas de parámetros tipados, descripciones semánticas y control de ejecución.
- **Lo que se va a crear:**
  - Crear `src/cognitive_assistant/shared/tools/registry.py`:
    - Clase `ToolRegistry` con métodos:
      - `register_tool(name: str, description: str, func: Callable, schema: dict)`
      - `execute_tool(name: str, args: dict, trace_id: str) -> dict`
    - Registrar herramienta `web_search_and_read`: Invoca `PlaywrightBrowserTool` o `FirecrawlTool` para extraer páginas web con resumen en Markdown.
    - Registrar herramienta `calculator_safe`: Evaluación matemática determinista sin acceso al sistema operativo.
- **Criterios de Aceptación:**
  - Registro de herramientas disponible para introspección y ejecución segura.

---

#### Etapa 4.2: Enriquecimiento del Grafo Cognitivo con Nodo ReAct (`tools_node`)
- **Explicación:**
  El grafo lineal de 3 nodos se transforma en un grafo con bifurcación condicional:
  ```text
  [perceive] -> [recall] -> [deliberate]
                                  │
                          ¿Requiere acción externa?
                         ├── Sí ──> [execute_tool] ──┐
                         └── No ─────────────────────┴──> [consolidate] ──> [FIN]
  ```
  El nodo `deliberate` evalúa si el usuario solicita información externa o navegación web. Si es necesario, genera una directiva de herramienta (`ToolCall`). El nodo `execute_tool` la ejecuta y añade el resultado al estado cognitivo para que la respuesta final sintetice la información extraída.
- **Lo que se va a modificar:**
  - Modificar `src/cognitive_assistant/modules/c4_executive/state.py`: Añadir campos `pending_tool_call: dict | None`, `tool_results: list[dict]`.
  - Modificar `src/cognitive_assistant/modules/c4_executive/graph.py`: Añadir nodo `execute_tool_node` y arista condicional `should_use_tool`.
- **Criterios de Aceptación:**
  - Peticiones sin herramientas no añaden sobrecosto de latencia.
  - Peticiones con intención de navegación web ejecutan la herramienta y consolidan el resultado en la respuesta final.

---

#### Etapa 4.3: Optimización de Timeouts y Resiliencia en Navegación Web
- **Explicación:**
  Para evitar que pruebas o consultas cuelguen el event loop ante URLs no disponibles (como ocurrió en la prueba de timeout de 30 segundos), se ajusta el timeout de Playwright a 5 segundos por defecto y se implementa un validador de URL seguro (rechazo de IPs privadas o bucles localhost no autorizados).
- **Lo que se va a modificar:**
  - Modificar `src/cognitive_assistant/shared/tools/web_browser.py`: Ajustar `default_timeout_ms = 5000` y añadir validación de esquema URL.
- **Criterios de Aceptación:**
  - Tiempo de ejecución de `test_web_tools.py` reducido de 185s a < 25s.

---

## 3. Análisis Exhaustivo de Inconsistencias: Planificado vs. Obtenido

En cumplimiento con la directiva de auditoría de código, se presenta la comparación crítica entre lo planificado en el Día 1 y el estado real del código fuente al inicio del Día 2:

| Componente / Área | Lo Planificado Inicialmente (Ayer) | Lo Obtenido en el Código (Hoy) | Inconsistencia / Brecha Identificada | Acción Correctiva Inmediata (Día 2) |
| :--- | :--- | :--- | :--- | :--- |
| **Puerto PostgreSQL** | Puerto estándar `5432` en Docker para `pgvector`. | En Windows existe un servicio nativo `postgres.exe` (PID 7208) escuchando en 5432. | **Colisión de puertos:** Las conexiones del host a 5432 conectan al postgres nativo o resetean el socket, saltándose el contenedor de Docker. | Reasignar el puerto exterior del contenedor a `5433:5432` en `docker-compose.yml`, `.env` y `settings.py`. |
| **Driver de DB en Windows** | Uso de `psycopg2-binary` para PostgreSQL y pgvector. | `psycopg2-binary` lanza `UnicodeDecodeError` en Windows por caracteres especiales en codepage local. | **Incompatibilidad de driver:** `test_pgvector_db.py` tuvo que ser marcado con `pytest.skip`. | Estandarizar toda la capa asíncrona sobre `asyncpg` puro y SQLAlchemy 2.0 Async en el puerto 5433. |
| **Auditoría Transaccional** | Modelo `AuditTransaction` persistiendo en PostgreSQL en cada request. | Registro únicamente en logs JSON y en respuesta HTTP (`X-Trace-ID`). | **Falta de persistencia en disco:** No existe aún la tabla `audit_transactions` en base de datos. | Construir `AuditService` y el modelo `AuditTransaction` en la Fase 1 del Día 2. |
| **Memoria de Trabajo** | Estado mental activo almacenado en Redis con latencia < 20 ms. | Grafo cognitivo sin retención de turnos previos (stateless por request). | **Falta de retención conversacional:** Cada petición olvida el contexto inmediato de la sesión anterior. | Implementar `WorkingMemoryManager` con Redis 7 y fallback local en la Fase 2 del Día 2. |
| **Gobernanza y Seguridad** | Filtro perimétrico contra Prompt Injections y Jailbreaks. | El endpoint `POST /reception/deliberate` pasa directo de Capa 2 a Capa 4 sin cortafuegos. | **Vulnerabilidad perimétrica:** Peticiones adversarias alcanzarían el LLM directamente. | Crear el módulo `c3_governance` y el interceptor `PromptGuard` en la Fase 3 del Día 2. |
| **Herramientas en LangGraph** | Integración de herramientas periféricas en el ciclo deliberativo. | `PlaywrightBrowserTool` existe en `shared/tools`, pero no está conectado a los nodos de LangGraph. | **Desconexión funcional:** El agente deliberativo no puede invocar de forma autónoma el navegador. | Conectar `ToolRegistry` y el nodo `execute_tool` en el grafo de LangGraph en la Fase 4 del Día 2. |
| **Timeout de Navegación** | Extracción web ágil para alimentar el contexto del LLM. | Timeout por defecto de 30 segundos bloqueaba la prueba local ante URLs no levantadas. | **Latencia excesiva en pruebas:** La suite tardó 3 minutos en completarse por el timeout de Playwright. | Reducir timeout a 5,000 ms y aislar navegación en mocks locales para pruebas rápidas. |

---

## 4. Protocolo Integral de Pruebas y Validación Automatizada

### Estado Actual de la Suite (Línea Base Día 1)
```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\moise\OneDrive\Desktop\cognitive-assistant
plugins: anyio-4.15.1, langsmith-0.14.4, asyncio-1.4.0

tests/test_cognitive_api.py::test_post_reception_deliberate PASSED       [  6%]
tests/test_cognitive_api.py::test_memory_api_endpoints PASSED            [ 12%]
tests/test_cognitive_executive.py::test_build_cognitive_graph PASSED     [ 18%]
tests/test_cognitive_executive.py::test_execute_cognitive_cycle PASSED   [ 25%]
tests/test_health.py::test_health_check_returns_200_and_ok_status PASSED [ 31%]
tests/test_health.py::test_health_check_trace_id_in_header PASSED        [ 37%]
tests/test_llm_gateway.py::test_llm_gateway_acompletion_mock_fallback PASSED [ 43%]
tests/test_memory_service.py::test_memory_service_add_and_search PASSED  [ 50%]
tests/test_pgvector_db.py::test_postgres_pgvector_live_connection SKIPPED [ 56%]
tests/test_trace.py::test_unique_trace_id_per_request PASSED             [ 62%]
tests/test_trace.py::test_propagates_custom_trace_id PASSED              [ 68%]
tests/test_trace.py::test_trace_id_in_json_log PASSED                    [ 75%]
tests/test_trace.py::test_reception_message_trace_propagation PASSED     [ 81%]
tests/test_web_tools.py::test_playwright_tool_instantiation PASSED       [ 87%]
tests/test_web_tools.py::test_firecrawl_tool_instantiation PASSED        [ 93%]
tests/test_web_tools.py::test_firecrawl_local_fallback PASSED            [100%]

================== 15 passed, 1 skipped in 185.35s (0:03:05) ==================
```

### Batería de Nuevas Pruebas a Implementar en el Día 2
Para validar las 4 Fases de desarrollo, se incorporarán las siguientes suites de prueba:

1. **`tests/test_audit_persistence.py`:**
   - Verifica la creación automática de tablas en PostgreSQL en puerto `5433`.
   - Verifica que tras un request `POST /reception/deliberate`, se consulta la tabla `audit_transactions` y se comprueba la existencia del registro con el `trace_id` exacto.
2. **`tests/test_working_memory.py`:**
   - Verifica la escritura y lectura atómica de `WorkingMemoryState` en Redis.
   - Verifica el límite de ventana deslizante (máximo 6 turnos).
   - Verifica el funcionamiento del fallback en memoria cuando Redis no está activo.
   - Simula el diálogo de 2 turnos demostrando persistencia del contexto (Escenario 1).
3. **`tests/test_governance.py`:**
   - Verifica que estímulos limpios pasan con `risk_score = 0.0`.
   - Verifica que inyecciones de prompt sintéticas (DAN, override, leak) son bloqueadas con HTTP 403 y `risk_score >= 0.7`.
   - Verifica que el intento de ataque es auditado en `audit_transactions` con la bandera de violación.
4. **`tests/test_tool_execution_graph.py`:**
   - Verifica que consultas con intención de cálculo o navegación disparan el nodo de herramienta en LangGraph.
   - Verifica que la respuesta sintetizada final incorpora los datos devueltos por la herramienta.
5. **Reactivación de `tests/test_pgvector_db.py`:**
   - Conexión real asíncrona a `localhost:5433` sin `pytest.skip`.

---

## 5. Matriz de Entregables Tangibles del Día 2

| Entregable | Ruta de Archivo | Responsabilidad / Capa |
| :--- | :--- | :--- |
| **Configuración de Red DB** | `docker-compose.yml`<br>`.env.example`<br>`settings.py` | Plano A: Reasignación a puerto `5433` para evitar colisión con PID 7208. |
| **Persistencia Asíncrona** | `shared/infrastructure/db.py`<br>`shared/infrastructure/models.py`<br>`shared/infrastructure/audit.py` | Plano B: Motor `asyncpg`, tabla `audit_transactions` y servicio de auditoría. |
| **Memoria de Trabajo** | `shared/infrastructure/redis_client.py`<br>`modules/c4_executive/working_memory.py` | Capa 4: Retención conversacional inmediata en Redis (< 20 ms). |
| **Cortafuegos Cognitivo** | `modules/c3_governance/schemas.py`<br>`modules/c3_governance/prompt_guard.py`<br>`modules/c3_governance/service.py` | Capa 3: Detección y bloqueo perimétrico de Prompt Injection con HTTP 403. |
| **Herramientas en Grafo** | `shared/tools/registry.py`<br>`modules/c4_executive/graph.py` | Capa 6/7: Ejecución ReAct de herramientas en el grafo de LangGraph. |
| **Suite de Tests Ampliada** | `tests/test_audit_persistence.py`<br>`tests/test_working_memory.py`<br>`tests/test_governance.py`<br>`tests/test_pgvector_db.py` | QA: Meta de >= 22 tests aprobados con 0 skipped. |
| **Informe de Avance Día 2** | `DATA/INFORMES/INFORME_AVANCE_DIA_2.md` | Documentación formal consolidada para la tesis. |

---
*Fin del Plan de Trabajo Maestro para el Día 2.*
