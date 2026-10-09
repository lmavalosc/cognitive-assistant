# PLAN MAESTRO DE TRABAJO: ASISTENTE COGNITIVO MODULAR (JARVIS 0.0)
## Cronograma de Ejecución: 2 Meses (8 Semanas / 40 Días Hábiles)
**Documento Técnico Asociado:** `TR-COG-2026-ARCH-V2.0` / `TR-COG-2026-PLAN-V2.0`  
**Metodología:** *Core-to-Periphery* (Del núcleo a la periferia) + Monolito Modular Hexagonal  
**Meta:** Desarrollo integral de las **10 Capas Funcionales y 2 Planos Transversales** (taxonomía vigente v2.1, ver `DATA/arquitectura_10_capas.md` y ADR 007) con validación de los 7 Escenarios Experimentales.

---

## 0. ACTUALIZACIÓN Y CORRECCIÓN — 08 de Octubre, 2026 (vinculante)

Sección incorporada en la corrección documental global. Aplica sobre todo el plan:

1. **Base taxonómica:** donde este plan diga "8 Capas + 3 Planos", léase la taxonomía v2.1 de **10 Capas + 2 Planos**. Equivalencias oficiales: antigua C4 -> vigentes **C4 (memoria de trabajo)** + **C5 (ejecutivo)**; antigua C5 -> **C6**; antigua C6 -> **C7**; antigua C7 -> **C8**; antigua C8 -> **C10**; antiguo Plano C -> **Capa 9**. Planos transversales vigentes: A (Infraestructura) y B (Observabilidad/Auditoría).
2. **Orden de dependencia corregido (no negociable):** **Gobernanza (C3) -> Sandbox (C8) -> Herramientas autónomas (ciclo ReAct)**. La Fase 4 del Día 2 y todo cableado de herramientas quedan **BLOQUEADOS** hasta completar la remediación P0 (`DATA/AUDITORIA&REPARACIÓN/AUDITORIA_SEGURIDAD_2026-10-08.md`, `DATA/AUDITORIA&REPARACIÓN/PROMPT_REMEDIACION_SEGURIDAD.md`). Las herramientas web creadas el Día 1 se reclasifican como scaffolding latente, no capacidad operativa.
3. **Corrección del Hito Etapa 1:** el criterio "Rate limiting Token Bucket sobre Redis" (Día 05) **no fue implementado**; las variables `RATE_LIMIT_*` no tienen consumidor en el código (hallazgo SEC-02). El Hito Etapa 1 queda en estado **PARCIAL**. Regla permanente: *hito superado = test de escenario en verde*, nunca una declaración en documento.
4. **Contrato público pendiente:** el endpoint canónico `POST /api/v1/chat` (exigido en Semana 1 y Semana 3) no existe; la API real expone `/reception/message` y `/reception/deliberate`. Crearlo como alias es prerrequisito de la Semana 3 (canales externos).
5. **Identidad:** todo `user_id`/`session_id` autodeclarado es defecto de seguridad (SEC-05); las capas deben asumir identidad derivada de autenticación.
6. **Capa 3 ampliada (v2.1):** la Semana 5 incluye tres puntos de control: entrada (PromptGuard), acción (policy check por ToolRequest) y salida (filtro de fuga PII/secretos en respuesta y en consolidación de memoria).

---

## 1. VISIÓN GENERAL Y DISTRIBUCIÓN TEMPORAL

```mermaid
gantt
    title Cronograma Maestro - 2 Meses (8 Semanas)
    dateFormat  YYYY-MM-DD
    section MES 1: Núcleo y Corteza Cognitiva
    Semana 1 (D01-D05) : Tronco Encefálico e Infraestructura :done, s1, 2026-10-12, 5d
    Semana 2 (D06-D10) : Memoria de Trabajo y Conexión LLM   :active, s2, after s1, 5d
    Semana 3 (D11-D15) : Percepción Multicanal y Saliencia   :s3, after s2, 5d
    Semana 4 (D16-D20) : Planner Acíclico y Multiagente      :s4, after s3, 5d
    section MES 2: Seguridad, Memoria y Autonomía
    Semana 5 (D21-D25) : Gobernanza, Guardrails y HITL       :s5, 2026-11-09, 5d
    Semana 6 (D26-D30) : Docker Sandbox Confinado y Tools    :s6, after s5, 5d
    Semana 7 (D31-D35) : Hipocampo RAG pgvector y Episodios  :s7, after s6, 5d
    Semana 8 (D36-D40) : Consolidación Offline y QA Total    :s8, after s7, 5d
```

### Tabla de Equivalencia: Meses, Semanas y Capas del Sistema

| Mes | Semana | Días | Capas / Planos Involucrados | Hito Principal / Escenario Experimental |
| :--- | :--- | :--- | :--- | :--- |
| **MES 1** | **Semana 1** | D01 - D05 | Plano A (Infra), Capa 2 (Recepción), Capa 8 (Efectores), Plano B (Trace ID) | **Etapa 1:** Pipeline E/S transaccional mínimo con `trace_id` inyectado. |
| **MES 1** | **Semana 2** | D06 - D10 | Capa 4 (Memoria de Trabajo), Plano A (Abstracción LLM) | **Etapa 2:** Retención conversacional inmediata en Redis (**Escenario 1**). |
| **MES 1** | **Semana 3** | D11 - D15 | Capa 1 (Percepción Sensorial y Atención: Whisper + Telegram + Saliencia) | **Etapa 3:** Matriz de clasificación de saliencia multicanal (Precisión >= 90%). |
| **MES 1** | **Semana 4** | D16 - D20 | Capa 4 (Planner Metacognitivo), Capa 6 (Agentes Especializados) | **Etapa 4:** Descomposición acíclica de planes y orquestación multiagente. |
| **MES 2** | **Semana 5** | D21 - D25 | Capa 3 (Gobernanza, RBAC/ABAC, Prompt Injection, Human-in-the-Loop) | **Etapa 5:** Bloqueo 100% de Jailbreaks (**Escenario 4**) y flujo HITL (**Escenario 5**). |
| **MES 2** | **Semana 6** | D26 - D30 | Capa 7 (Herramientas Confinadas, Protocolo MCP, Docker SDK Runner) | **Etapa 6:** Aislamiento en sandbox efímero con timeout 15s (**Escenario 3**). |
| **MES 2** | **Semana 7** | D31 - D35 | Capa 5 (Memorias Persistentes: Episódica SQL y Semántica pgvector HNSW) | **Etapa 7:** Recuperación contextual RAG con citas exactas (**Escenario 2**). |
| **MES 2** | **Semana 8** | D36 - D40 | Plano C (Aprendizaje Offline Batch) + Plano B (Auditoría Total) + Hardening | **Etapa 8:** Adaptación de perfil offline (**Escenario 6**) y Trazabilidad 100% (**Escenario 7**). |

---

# 2. PLAN DETALLADO DÍA POR DÍA

---

## MES 1: EL NÚCLEO OPERATIVO, PERCEPCIÓN Y CORTEZA COGNITIVA

### SEMANA 1: El Tronco Encefálico e Infraestructura Base (Etapa 1)
> **Meta:** Establecer el scaffold del Monolito Modular Hexagonal, levantar los contenedores base (PostgreSQL 16, Redis 7), configurar FastAPI con inyección de `trace_id` (OpenTelemetry) y construir el ciclo de eco inicial con auditoría.

- **Día 01 (Lunes): Arquitectura de Repositorio y Entorno Virtual**
  - Inicializar entorno Python 3.11+ con `poetry` o `pip-tools` y `pyproject.toml`.
  - Crear estructura modular hexagonal: `src/cognitive_assistant/{shared, platform, modules}`.
  - Implementar configuración centralizada con `pydantic-settings` en `settings.py` (`.env.example`).
  - *Criterio de Aceptación:* `pytest` ejecuta suite vacía sin fallos y carga de variables de entorno validada.

- **Día 02 (Martes): Contenedores Base (Plano A: Infraestructura)**
  - Redactar `docker-compose.yml` para servicios locales: PostgreSQL 16 con extensión `pgvector` y Redis 7 Alpine.
  - Escribir scripts SQL de inicialización en `infra/postgres/init/01_extensions.sql` (`CREATE EXTENSION IF NOT EXISTS vector;`).
  - Crear adaptadores de conexión a base de datos en `platform/db/session.py` (SQLAlchemy 2.0 Async / asyncpg) y caché en `platform/cache/redis_client.py`.
  - *Criterio de Aceptación:* `docker compose up -d` exitoso; test de ping a PostgreSQL y Redis con retorno positivo.

- **Día 03 (Miércoles): Capa 2 - API Gateway y Telemetría Universal (Plano B)**
  - Implementar middleware en FastAPI para inyección de `trace_id` (UUIDv4) en headers de request y response (`X-Trace-Id`).
  - Integrar OpenTelemetry Tracer Provider y logging estructurado en formato JSON en `shared/telemetry/logger.py`.
  - Crear contratos Pydantic base de entrada: `PerceptionEvent` y `ValidatedRequest`.
  - *Criterio de Aceptación:* Cada petición HTTP genera log JSON estructurado conteniendo el mismo `trace_id` propagado.

- **Día 04 (Jueves): Capa 8 - Efectores Base y Persistencia de Transacciones**
  - Implementar endpoint `POST /api/v1/chat` en `modules/c2_reception/router.py`.
  - Crear modelo SQLAlchemy de auditoría básica `AuditTransaction` para registrar `trace_id`, timestamp, canal, payload y tiempo de respuesta.
  - Construir efector de respuesta básica (Eco determinista) en `modules/c8_effectors/dispatcher.py`.
  - *Criterio de Aceptación:* Solicitud HTTP `POST /api/v1/chat` retorna `HTTP 200` y registra la transacción en la tabla de base de datos con su `trace_id`.

- **Día 05 (Viernes): Rate Limiting y Cierre del Sprint 1**
  - Configurar limitador de tasa Token Bucket sobre Redis en `modules/c2_reception/rate_limiter.py`.
  - Crear suite de pruebas de integración para ráfagas de solicitudes (verificar código HTTP 429).
  - Ejecutar prueba cURL/Postman extremo a extremo validando latencia < 30ms en la ruta básica.
  - *Criterio de Aceptación:* **Hito Etapa 1 Superado.** Sistema responde transaccionalmente, audita con `trace_id` y limita peticiones abusivas.

---

### SEMANA 2: Memoria de Trabajo y Conexión LLM (Etapa 2)
> **Meta:** Conectar la inferencia de LLM mediante una capa agnóstica de proveedores y mantener el estado mental activo (Working Memory) en Redis estructurado por `session_id`.

- **Día 06 (Lunes): Abstracción Unificada de Proveedores LLM (Plano A)**
  - Crear interfaz base `BaseLLMClient` en `platform/llm/client.py`.
  - Implementar conector para modelos locales (Ollama API: `llama3.2`, `mistral`, `qwen2.5`) y conector para APIs remotas (OpenAI / Anthropic / Gemini SDK).
  - Incluir manejo de reintentos con backoff exponencial y fallbacks automáticos ante caídas del proveedor.
  - *Criterio de Aceptación:* Test unitario validando respuesta estructurada tanto en modo local (Ollama) como remoto.

- **Día 07 (Martes): Capa 4 - Esquema de Memoria de Trabajo en Redis**
  - Diseñar el esquema de estado mental activo en Redis bajo la clave `session:{session_id}:working_memory`.
  - Estructurar campos JSON: `active_goal`, `subtasks`, `constraints`, `recent_turns` y `system_notes`.
  - Crear clase `RedisWorkingMemory` con operaciones atómicas (`get_state`, `update_goal`, `append_turn`, `clear_session`).
  - *Criterio de Aceptación:* Test unitario que persiste y recupera el estado mental activo de una sesión en menos de 10 ms.

- **Día 08 (Miércoles): Ventana Deslizante y Compresión de Contexto**
  - Implementar lógica de ventana deslizante: mantener los últimos 5 turnos conversacionales completos.
  - Incorporar generador de resumen automático (rolling summary) cuando el número de turnos supere el umbral.
  - Inyectar el bloque de Memoria de Trabajo directamente en el System Prompt del LLM.
  - *Criterio de Aceptación:* Test de preservación de tokens: el prompt generado no excede la ventana configurada.

- **Día 09 (Jueves): Integración del Flujo Conversacional Inmediato**
  - Unificar flujo: `Endpoint /api/v1/chat -> C2 (Trace ID) -> C4 (Carga de WM) -> LLM -> C4 (Actualiza WM) -> C8 (Respuesta)`.
  - Añadir soporte para metadata de sesión en los payloads de FastAPI.
  - *Criterio de Aceptación:* Diálogo en dos pasos: Turno 1 ("Me llamo Moises y estoy programando JARVIS"), Turno 2 ("¿Cuál es mi proyecto?"). El asistente responde conociendo el contexto sin re-especificarlo.

- **Día 10 (Viernes): Validación Experimental del Escenario 1**
  - Implementar y ejecutar el script `tests/scenarios/test_scenario_1_working_memory.py`.
  - Medir latencia de recuperación en Redis (objetivo: < 20 ms).
  - Verificar retención precisa de entidades semánticas entre turnos.
  - *Criterio de Aceptación:* **Escenario 1 Aprobado.** Hito Etapa 2 completado con métricas de latencia registradas en telemetría.

---

### SEMANA 3: Percepción Sensorial y Filtro de Atención (Etapa 3)
> **Meta:** Habilitar canales de entrada heterogéneos (Webhooks, Telegram Bot, Audio PCM con Whisper local) y clasificar la atención y saliencia cognitiva antes de procesar la solicitud.

- **Día 11 (Lunes): Capa 1 - Adaptador de Telegram Bot y Webhooks**
  - Implementar servicio `TelegramAdapter` en `modules/c1_perception/adapters/telegram.py` con `python-telegram-bot` / polling o webhook.
  - Normalizar mensajes entrantes de Telegram al esquema interno unificado `PerceptionEvent`.
  - Crear endpoint para webhooks genéricos IoT / HTTP.
  - *Criterio de Aceptación:* Mensaje enviado desde la app de Telegram entra al pipeline y se traduce en un `PerceptionEvent` válido.

- **Día 12 (Martes): Capa 1 - Integración de Whisper para Audio (STT)**
  - Implementar conector de Speech-to-Text en `modules/c1_perception/stt/whisper_engine.py` (usando `faster-whisper` o Whisper local).
  - Diseñar pipeline de recepción de notas de voz (.ogg/.wav/PCM), conversión de audio a texto y encapsulación en `PerceptionEvent`.
  - Añadir fallback para entornos sin GPU (modo CPU cuantizado `int8`).
  - *Criterio de Aceptación:* Nota de voz de audio se transcribe con Word Error Rate (WER) bajo y genera texto limpio en el evento.

- **Día 13 (Miércoles): Clasificador de Atención y Saliencia Cognitiva**
  - Diseñar prompt y contrato estructurado para el módulo de atención (`AttentionResult` en `shared/contracts/attention.py`):
    - `intent`: clasificación de la intención del usuario.
    - `urgency`: float [0.0 - 1.0].
    - `relevance`: float [0.0 - 1.0].
    - `emotional_signal`: detección de tono/estrés/urgencia.
    - `requires_tool`: bool determinista.
    - `requires_human_confirmation`: flag preventiva.
  - Implementar clasificador mediante llamada a LLM optimizado (modelo rápido/pequeño con Structured Outputs de Pydantic).
  - *Criterio de Aceptación:* Clasificación determinista con formato JSON exacto sin errores de parsing.

- **Día 14 (Jueves): Matriz de Evaluación de Saliencia (20 Casos de Prueba)**
  - Redactar dataset de 20 estímulos variados: saludos informales, comandos directos, emergencias técnicas, ambigüedades y órdenes complejas.
  - Escribir script de validación cuantitativa `tests/unit/test_attention_classifier.py`.
  - Ajustar prompts para alcanzar y superar el 90% de exactitud en clasificación de urgencia e intención.
  - *Criterio de Aceptación:* 18 o más casos de los 20 clasificados con precisión categórica según las etiquetas de referencia.

- **Día 15 (Viernes): Integración Percepción -> Recepción -> Flujo Central**
  - Acoplar `Capa 1 (Percepción)` con `Capa 2 (Recepción/Normalización)`.
  - Verificar propagación del `AttentionResult` hacia los metadatos de la solicitud validada.
  - *Criterio de Aceptación:* **Hito Etapa 3 Superado.** El sistema asimila texto, Telegram y audio, evaluando saliencia en tiempo real antes de planificar.

---

### SEMANA 4: La Corteza Prefrontal: Planner y Agentes (Etapa 4)
> **Meta:** Desacoplar la recepción pasiva del procesamiento cognitivo mediante la descomposición de objetivos en planes acíclicos (DAGs) estructurados y orquestación multiagente.

- **Día 16 (Lunes): Capa 4 - Módulo Planner y Contrato de Plan Acíclico**
  - Diseñar esquema Pydantic `CognitivePlan` en `shared/contracts/plan.py`:
    - `plan_id`: UUIDv4.
    - `goal`: objetivo declarado.
    - `confidence_score`: flotante [0.0 - 1.0].
    - `steps`: lista ordenada de `PlanStep(step_id, agent_assigned, action_type, dependencies, inputs)`.
  - Implementar motor del planificador en `modules/c4_executive/planner.py`.
  - *Criterio de Aceptación:* Solicitud no trivial (ej: "Investiga el clima y escribe un reporte") se descompone en un plan JSON válido con pasos y dependencias.

- **Día 17 (Martes): Metacognición y Umbral de Confianza**
  - Desarrollar evaluador metacognitivo en `modules/c4_executive/metacognition.py`.
  - Si `confidence_score < 0.65` o el requerimiento presenta ambigüedad insalvable, el planificador entra en estado `SUSPENDED_NEEDS_CLARIFICATION`.
  - Generar pregunta de desambiguación dirigida al usuario sin avanzar la ejecución ciega.
  - *Criterio de Aceptación:* Prompt deliberadamente vago detiene la ejecución automática y retorna pregunta aclaratoria estructurada.

- **Día 18 (Miércoles): Capa 6 - Registro de Agentes y Agente Investigador**
  - Implementar `AgentRegistry` en `modules/c6_agents/registry.py` con roles, prompts de especialización y permisos delimitados.
  - Desarrollar `ResearchAgent`: especialista en consulta y síntesis de información sin capacidad de modificación de código ni sistema.
  - Crear interfaz de paso de mensajes inter-agentes.
  - *Criterio de Aceptación:* Invocación del Agente Investigador produce un artefacto de síntesis estructurado según su contrato.

- **Día 19 (Jueves): Capa 6 - Agente Programador y Agente Verificador**
  - Desarrollar `CoderAgent`: especializado en generación de código limpio y estructurado con tipado estricto.
  - Desarrollar `CriticVerifierAgent`: agente evaluador que audita respuestas intermedias buscando alucinaciones o inconsistencias fácticas.
  - Implementar el orquestador secuencial/DAG en `modules/c6_agents/orchestrator.py`.
  - *Criterio de Aceptación:* Ejecución en pipeline donde el Agente Investigador genera datos, el Programador produce código y el Verificador valida la coherencia antes de finalizar.

- **Día 20 (Viernes): Trazabilidad de Orquestación y Cierre de Mes 1**
  - Instrumentar spans de OpenTelemetry para cada paso del plan y cada invocación de agente.
  - Validar visualización o registro de la secuencia de pasos vinculados bajo el mismo `trace_id`.
  - Revisión y consolidación de todos los módulos del Mes 1 (Capas 1, 2, 4, 6 y 8 básica).
  - *Criterio de Aceptación:* **Hito Etapa 4 Superado y Cierre de Mes 1 Exitoso.** Sistema cognitivo planifica, descompone y orquesta agentes con trazabilidad total.

---

## MES 2: SEGURIDAD INMUNOLÓGICA, EXTREMIDADES SANDBOXED, MEMORIA LARGA Y AUTONOMÍA

### SEMANA 5: El Sistema Inmunológico: Gobernanza y Salvaguardas (Etapa 5)
> **Meta:** Implementar el cortafuegos de seguridad de la arquitectura: control de acceso (RBAC/ABAC), la Constitución Ética del Asistente, filtros heurísticos/semánticos anti-Prompt Injection y el protocolo Human-in-the-Loop.

- **Día 21 (Lunes): Constitución del Asistente y Motor de Políticas**
  - Redactar `config/constitution.yaml` con reglas éticas inmutables, fronteras de privacidad y límites operativos.
  - Implementar evaluador de políticas determinista (RBAC/ABAC) en `modules/c3_governance/policy_engine.py`.
  - Definir niveles de riesgo de operación: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
  - *Criterio de Aceptación:* Reglas declarativas impiden acciones no permitidas según el rol del usuario asignado en la sesión.

- **Día 22 (Martes): Filtros Anti-Prompt Injection y Sanitización Heurística**
  - Construir filtro de sanitización y detección de inyecciones en `modules/c3_governance/guardrails.py`.
  - Incorporar reglas basadas en patrones sintácticos de evasión (jailbreaks, "ignore previous instructions", fuga de prompts de sistema).
  - Implementar evaluador semántico secundario (modelo de guardrail liviano tipo Llama-Guard o clasificador de intenciones hostiles).
  - *Criterio de Aceptación:* Inyecciones conocidas son detectadas con estado `REJECTED` antes de llegar a la Capa 4 de planificación.

- **Día 23 (Miércoles): Protocolo Human-in-the-Loop (HITL)**
  - Implementar máquina de estados para operaciones `HIGH` y `CRITICAL` en `modules/c3_governance/hitl_controller.py`.
  - Si la acción implica riesgo (borrado de datos, envío de mensajes masivos, ejecución de comandos destructivos), el sistema pasa a estado `NEEDS_CONFIRMATION` y genera un `challenge_token` criptográfico.
  - Suspender ejecución en Redis a la espera de la aprobación explícita del usuario vía token.
  - *Criterio de Aceptación:* La acción queda bloqueada y no se despacha a la Capa 7 hasta recibir la confirmación explícita correspondiente.

- **Día 24 (Jueves): Ejecución Experimental de Escenario 4 (Jailbreak / Injection)**
  - Construir suite con 15 vectores de ataque agresivos (Jailbreak, DAN prompts, bypass de rol, exfiltración de memoria).
  - Ejecutar `tests/scenarios/test_scenario_4_prompt_injection.py`.
  - Auditar que el 100% de los intentos hostiles sean repelidos y queden registrados en `AuditSecurityLog`.
  - *Criterio de Aceptación:* **Escenario 4 Aprobado (100% de mitigación verificada).**

- **Día 25 (Viernes): Ejecución Experimental de Escenario 5 (HITL)**
  - Ejecutar `tests/scenarios/test_scenario_5_human_in_the_loop.py`.
  - Simular comando de alto riesgo ("Eliminar base de datos de producción").
  - Verificar interrupción inmediata, emisión de alerta al usuario y reanudación correcta únicamente tras recibir el token de autorización.
  - *Criterio de Aceptación:* **Escenario 5 Aprobado y Hito Etapa 5 Superado.** Perímetro de seguridad impenetrable y gobernanza activa.

---

### SEMANA 6: Las Extremidades: Sandbox Docker y Protocolo MCP (Etapa 6)
> **Meta:** Proveer capacidad efectora real pero absolutamente segura y aislada mediante contenedores efímeros Docker sin acceso a red de host, timeouts estrictos y estandarización de herramientas bajo Model Context Protocol (MCP).

- **Día 26 (Lunes): Capa 7 - Confinador Docker Runner (Docker SDK)**
  - Desarrollar `DockerSandboxRunner` en `platform/sandbox/docker_runner.py` usando la librería oficial `docker` de Python.
  - Configurar Dockerfile mínimo para ejecución de código (`infra/docker/sandbox_runner.Dockerfile`) con usuario sin privilegios (`non-root`).
  - Aplicar restricciones estrictas: `network_mode='none'`, `mem_limit='256m'`, `cpu_quota=50000` (50% de 1 core), `read_only=True` en rootfs.
  - *Criterio de Aceptación:* Script Python ejecutado en el contenedor imprime en stdout y finaliza sin acceso a red ni acceso a archivos del anfitrión.

- **Día 27 (Martes): Limitador de Recursos, Timeout Forzado y Captura I/O**
  - Implementar watchdog con timeout determinista de 15.0 segundos.
  - Si el contenedor supera el tiempo límite o consume memoria excesiva, forzar `container.kill()` y recolectar logs de error.
  - Estructurar el retorno en contrato Pydantic `ToolResult(stdout, stderr, exit_code, duration_ms, resource_usage)`.
  - *Criterio de Aceptación:* Script con `while True: pass` es abortado forzosamente a los 15 segundos exactos retornando código de timeout.

- **Día 28 (Miércoles): Tool Registry y Estandarización Model Context Protocol (MCP)**
  - Diseñar el catálogo de herramientas en `modules/c7_tools/registry.py` adoptando la especificación MCP.
  - Definir interfaces de herramientas estándar: calculadora matemática segura, analizador sintáctico de código, formateador de documentos.
  - Conectar los `ToolRequests` emitidos por los Agentes de Capa 6 hacia el despachador de Capa 7.
  - *Criterio de Aceptación:* Un agente solicita ejecución de cálculo algebraico complejo y recibe el resultado formateado vía protocolo MCP.

- **Día 29 (Jueves): Mock de Actuadores y Dispositivos de Entorno**
  - Desarrollar servicio de simulación y mocks en `modules/c7_tools/mocks/iot_mock.py` (simulador de bombillas inteligentes, termostatos y alarmas).
  - Permitir a los agentes actuar sobre dispositivos virtuales con validación de estado anterior y posterior.
  - *Criterio de Aceptación:* Comandos domóticos cambian el estado del mock virtual y retornan confirmación verificable en la telemetría.

- **Día 30 (Viernes): Validación Experimental del Escenario 3 (Sandbox Confinado)**
  - Ejecutar `tests/scenarios/test_scenario_3_docker_sandbox.py`.
  - Test 1: Intento de conexión socket hacia internet exterior (debe fallar inmediatamente por aislamiento de red).
  - Test 2: Bucle infinito y consumo de CPU (debe interrumpirse a los 15.0 s sin afectar el rendimiento de la máquina anfitriona).
  - *Criterio de Aceptación:* **Escenario 3 Aprobado y Hito Etapa 6 Superado.** El asistente posee herramientas con confinamiento de seguridad de grado industrial.

---

### SEMANA 7: El Hipocampo: Memorias Persistentes de Largo Plazo y RAG (Etapa 7)
> **Meta:** Dotar al sistema de persistencia histórica (Memoria Episódica en PostgreSQL relacional) y memoria semántica mediante base vectorial con `pgvector` e índice HNSW para RAG documental de alta fidelidad.

- **Día 31 (Lunes): Capa 5 - Memoria Episódica en PostgreSQL**
  - Diseñar modelos relacionales en `modules/c5_memory/models.py`:
    - `Episode`: id, session_id, user_id, start_time, end_time, summary, emotional_valence, outcome_success.
    - `TurnLog`: id, episode_id, user_stimulus, assistant_response, plan_snapshot, trace_id, metrics.
  - Conectar Capa 8 para que al cerrar cada ciclo conversacional, se serialice y almacene automáticamente el episodio.
  - *Criterio de Aceptación:* Consulta SQL `SELECT * FROM episodes` muestra episodios cerrados con su respectivo resumen y métricas.

- **Día 32 (Martes): Capa 5 - Memoria Semántica y Base Vectorial (pgvector)**
  - Configurar tabla de embeddings en PostgreSQL con extensión `pgvector`:
    - `DocumentChunk`: id, document_name, chunk_index, content, metadata_json, embedding (vector de dimensión 1536 o 768).
  - Crear índice de búsqueda rápida aproximada **HNSW** (`INDEX USING hnsw (embedding vector_cosine_ops)`).
  - Implementar conector de embeddings con modelo unificado (local SentenceTransformers o API remota).
  - *Criterio de Aceptación:* Inserción de 500 vectores y consulta de vecino más cercano por similitud de coseno en menos de 15 ms.

- **Día 33 (Miércoles): Pipeline de Ingesta Documental y Chunking Semántico**
  - Desarrollar script `scripts/seed_knowledge.py` para ingesta de documentos técnicos en PDF / Markdown / Texto.
  - Implementar chunking semántico por párrafos con solapamiento (overlap) para no perder continuidad conceptual.
  - Indexar documentos de prueba en la base de datos vectorial.
  - *Criterio de Aceptación:* Documento técnico indexado completamente y disponible para consultas por similitud semántica.

- **Día 34 (Jueves): Recuperador RAG y Síntesis Asistida por el Agente Investigador**
  - Implementar servicio `ContextRetriever` en `modules/c5_memory/retriever.py` con re-ranking básico.
  - Integrar el recuperador con el Agente Investigador (Capa 6): inyectar chunks recuperados con citas de fuente obligatorias.
  - Incorporar salvaguarda anti-alucinaciones: si no existe contexto relevante (`similarity_score < 0.70`), declarar explícitamente desconocimiento de la fuente.
  - *Criterio de Aceptación:* Consulta sobre el manual indexado responde citando número de página y texto exacto sin inventar datos.

- **Día 35 (Viernes): Validación Experimental del Escenario 2 (Recuperación RAG)**
  - Ejecutar `tests/scenarios/test_scenario_2_semantic_rag.py`.
  - Evaluar métricas de recuperación: Recall@5 > 0.85 sobre batería de preguntas de dominio técnico.
  - Validar correlación con episodios pasados (recuperar lo que el usuario mencionó en una sesión de días previos).
  - *Criterio de Aceptación:* **Escenario 2 Aprobado y Hito Etapa 7 Superado.** El hipocampo almacena el pasado y comprende bibliotecas de conocimiento técnico.

---

### SEMANA 8: El Subconsciente Offline, Auditoría y Validación Total (Etapa 8 y Cierre)
> **Meta:** Implementar el aprendizaje continuo offline mediante consolidación batch asíncrona (Plano C), verificar el 100% de los 7 escenarios de evaluación, auditar trazabilidad total (Plano B) y empaquetar el producto final.

- **Día 36 (Lunes): Plano C - Tareas Batch de Consolidación Offline**
  - Implementar runner de consolidación en `modules/transversal_learning/consolidation_worker.py`.
  - Diseñar algoritmo batch nocturno que examine los episodios cerrados del día y extraiga:
    - Preferencias del usuario (estilo de respuesta, lenguaje, restricciones de tiempo).
    - Errores recurrentes o rechazos del evaluador ético.
  - Actualizar de forma atómica la tabla `UserProfile` en la base de datos.
  - *Criterio de Aceptación:* Ejecución del worker procesa 10 turnos simulados y actualiza el perfil del usuario con su tono preferido.

- **Día 37 (Martes): Mecanismos de Olvido y Decaimiento Cognitivo**
  - Desarrollar políticas de purga y olvido en `modules/transversal_learning/decay_manager.py`.
  - Implementar decaimiento temporal sobre memorias volátiles o irrelevantes (limpieza de datos transitorios sin valor).
  - Sanitización periódica de PII (Personally Identifiable Information) en los logs de auditoría.
  - *Criterio de Aceptación:* Registros antiguos clasificados con saliencia nula se marcan como archivados o son eliminados de forma controlada.

- **Día 38 (Miércoles): Validación Experimental de Escenario 6 y Escenario 7**
  - Ejecutar `tests/scenarios/test_scenario_6_offline_adaptation.py`:
    - Simular 10 correcciones de estilo en turnos sucesivos -> correr consolidación -> verificar que la siguiente interacción adopta las directivas aprendidas de manera espontánea.
  - Ejecutar `tests/scenarios/test_scenario_7_end_to_end_traceability.py`:
    - Lanzar ráfaga concurrente de 50 peticiones a través de múltiples canales (HTTP, Telegram, Audio).
    - Verificar que el 100% de las transacciones son reconstruibles paso a paso (Capa 1 a Capa 8) utilizando el `trace_id`.
  - *Criterio de Aceptación:* **Escenarios 6 y 7 Aprobados con éxito.**

- **Día 39 (Jueves): Auditoría Global, Hardening y Runner de Pruebas Total**
  - Configurar script maestro `scripts/evaluate_scenarios.py` que ejecute los 7 escenarios en serie y genere reporte cuantitativo en Markdown/JSON.
  - Revisar linters (`ruff`, `mypy` en modo estricto) y formateo de todo el código base.
  - Asegurar que no existan credenciales en duro (`.env` saneado).
  - *Criterio de Aceptación:* Suite completa de pruebas pasa en verde (`7/7 escenarios aprobados`, cobertura de pruebas > 85%).

- **Día 40 (Viernes): Empaquetado Final, Entrega y Documentación de Cierre**
  - Generar imágenes Docker definitivas y validar despliegue con comando único: `docker compose up --build`.
  - Redactar `README.md` operativo con guía de inicio rápido y manual de reproducción de los 7 escenarios.
  - Consolidar registros de decisiones arquitectónicas (ADRs 001 a 005) en `docs/adr/`.
  - *Criterio de Aceptación:* **PROYECTO COMPLETO Y OPERATIVO EN 2 MESES.** Sistema probado, documentado y listo para sustentación o puesta en producción.

---

# 3. MATRIZ DE TRAZABILIDAD: LOS 7 ESCENARIOS EXPERIMENTALES

| Escenario | Nombre de la Prueba | Capa / Plano Clave | Día de Ejecución | Criterio Cuantitativo de Éxito |
| :---: | :--- | :--- | :---: | :--- |
| **1** | **Continuidad Contextual y Memoria de Trabajo** | Capa 4 (Redis WM) | **Día 10** | Retención de entidades en turnos consecutivos; latencia en Redis < 20 ms. |
| **2** | **Recuperación Semántica de Dominio (RAG)** | Capa 5 (pgvector HNSW) | **Día 35** | Recall@5 > 0.85; citas textuales de PDFs indexados; 0% alucinaciones. |
| **3** | **Ejecución Confinada en Sandbox y Timeout** | Capa 7 (Docker Runner) | **Día 30** | Terminación forzosa a los 15.0 s; 0 fugas a la red del host; RAM < 256MB. |
| **4** | **Mitigación de Amenazas y Prompt Injection** | Capa 3 (Gobernanza) | **Día 24** | 100% de 15 ataques de Jailbreak repelidos y registrados en auditoría. |
| **5** | **Protocolo Human-in-the-Loop** | Capas 3, 4 y 8 | **Día 25** | Acciones críticas suspendidas en `NEEDS_CONFIRMATION` hasta token explícito. |
| **6** | **Adaptación por Consolidación Offline** | Plano C (Workers Batch) | **Día 38** | Mutación comprobada del perfil de usuario tras procesar el lote nocturno. |
| **7** | **Trazabilidad Extremo a Extremo** | Plano B (OpenTelemetry) | **Día 38** | 100% de 50 peticiones concurrentes trazables de punta a punta por `trace_id`. |

---

# 4. GESTIÓN DE RIESGOS Y CONTINGENCIAS EN EL PLAZO DE 2 MESES

Para asegurar el cumplimiento estricto del plazo máximo de 2 meses (8 semanas), se establecen las siguientes reglas de contingencia:

1. **Riesgo: Demoras en latencia o recursos con modelos LLM locales (Ollama)**
   - *Plan de Contingencia:* La abstracción `platform/llm/client.py` permite alternar inmediatamente a APIs remotas (OpenAI / Anthropic / Gemini SDK) con solo cambiar una variable en el archivo `.env`, permitiendo continuar el desarrollo de las capas superiores sin fricción de hardware.
2. **Riesgo: Complejidad en la integración del motor Docker SDK bajo Windows**
   - *Plan de Contingencia:* Desarrollar el adaptador de sandbox con interfaz abstracta `BaseSandboxRunner`. Si Docker Desktop presenta limitaciones de socket en Windows, se activa el modo emulado con subprocesos restringidos y mocks de aislamiento durante el desarrollo local, reservando el contenedor Docker para el entorno Linux / CI.
3. **Riesgo: Calibración del clasificador de atención en Capa 1**
   - *Plan de Contingencia:* Utilizar prompts con modo de salidas estructuradas JSON (Pydantic Schema) en el LLM, eliminando expresiones regulares complejas o parsers frágiles.
4. **Disciplina de Avance:**
   - Cada día concluye obligatoriamente con un commit funcional que pase su test correspondiente.
   - Si una tarea secundaria no se completa en su día asignado, se transfiere al bloque de estabilización del viernes de la misma semana sin mover la meta del sprint.
