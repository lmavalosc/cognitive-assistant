# ESPECIFICACIÓN TÉCNICA Y REQUISITOS — FASE 4: CICLO DE HERRAMIENTAS AUTÓNOMAS (ReAct)
## Proyecto de Tesis: Asistente Cognitivo Modular (JARVIS 0.0)
**Código de Documento:** `TR-COG-2026-FASE4-SPEC`  
**Taxonomía Vigente:** 10 Capas Funcionales + 2 Planos Transversales (`DATA/arquitectura_10_capas.md`, ADR 007)  
**Dependencias Prerrequisito:** Fase 1 (Persistencia), Fase 2 (Redis Working Memory), Fase 3 (Cortafuegos Capa 3 y Hardening P0/P1) — **COMPLETADAS Y CERRADAS**  
**Rama de Trabajo:** `semana1-tronco-encefalico`  

---

## 1. Diagnóstico de Estado y Balance de Avance (Días 1 a 4)

### ¿Vamos bien con el avance del Día 3 y 4?
**El proyecto se encuentra no solo al día, sino significativamente adelantado respecto al cronograma base.**

En el plan maestro de 8 semanas ([`PLAN_DE_TRABAJO_8_SEMANAS.md`](file:///c:/Users/moise/OneDrive/Desktop/cognitive-assistant/DATA/plan_de_trabajo/PLAN_DE_TRABAJO_8_SEMANAS.md)):
- El **Día 03 y Día 04** originales solo contemplaban levantar el logging JSON, el `trace_id` y un endpoint de eco básico (`POST /api/v1/chat`).
- La **Memoria de Trabajo en Redis** estaba prevista recién para la **Semana 2 (Días 06–10)**.
- El **Cortafuegos Heurístico, Anti-Jailbreak y Gobernanza de Capa 3** estaba planificado para la **Semana 5 (Días 21–25)**.
- El **Rate Limiting Token Bucket sobre Redis** era entregable del Día 05.

**Lo que ya está cerrado y funcionando hoy en tu código:**
1. **Infraestructura y Persistencia Real (Fase 1):** PostgreSQL 16 con `pgvector` en puerto 5433, SQLAlchemy 2.0 Async, modelo inmutable `AuditTransaction` y `AuditService` persistiendo en base de datos.
2. **Memoria Activa en Tiempo Real (Fase 2):** Redis 7 con `WorkingMemoryManager` (ventana de 6 turnos, TTL 24h, namespace `user:{id}:session:{id}:wm`) integrado en los 3 nodos de LangGraph.
3. **Cortafuegos Cognitivo y Blindaje P0/P1 (Fase 3):** PromptGuard determinista (<1ms), normalización NFKC, sanitización de caracteres nulos, filtro de datos sensibles antes de Mem0, autenticación `X-API-Key`, Rate Limiting Token Bucket, validador anti-SSRF y scrubbing de PII.
4. **Calidad y Estabilidad:** **46 pruebas unitarias y de integración pasando en verde** (`pytest -q`).

---

## 2. Visión y Objetivo de la Fase 4

La **Fase 4** convierte al Asistente Cognitivo desde un sistema de conversación puramente reactivo y estático hacia un **agente neuro-deliberativo con capacidad de interacción con el entorno (Razonamiento + Acción / ReAct)**.

### Cadena de Dependencia Arquitectónica (Innegociable)
```text
┌────────────────────────────────────────────────────────┐
│ Capa 3.a: Cortafuegos Perimétrico de Entrada (CERRADO) │
└──────────────────────────┬─────────────────────────────┘
                           │ Estímulo seguro
                           ▼
┌────────────────────────────────────────────────────────┐
│ Capa 5: Ejecutivo Cognitivo (LangGraph Deliberation)   │
└──────────────────────────┬─────────────────────────────┘
                           │ Propuesta de acción (ToolRequest)
                           ▼
┌────────────────────────────────────────────────────────┐
│ Capa 3.b: Gobernanza de Acción (ActionPolicyService)   │  <-- Fase 4
└──────────────────────────┬─────────────────────────────┘
                           │ Acción autorizada
                           ▼
┌────────────────────────────────────────────────────────┐
│ Capa 8: Sandbox Confinado de Herramientas (ToolRegistry)│  <-- Fase 4
└────────────────────────────────────────────────────────┘
```

---

## 3. Desglose de Componentes Necesarios para la Fase 4

### A. Capa 8: Catálogo y Sandbox Tipado de Herramientas (`ToolRegistry`)
**Ubicación:** `src/cognitive_assistant/shared/tools/registry.py`

#### 1. Esquemas y Contratos Pydantic v2
* `ToolRiskLevel` (Enum):
  * `LOW`: Operaciones deterministas puras en memoria, sin red externa ni efectos secundarios (ej. cálculos).
  * `MED`: Lecturas de red saliente controlada, con validación anti-SSRF forzosa (ej. web scraping).
  * `HIGH`: Modificación de estado interno o consultas a APIs autenticadas con secretos.
  * `CRITICAL`: Comandos de sistema, operaciones financieras o potencialmente destructivas (exige confirmación humana HITL obligatoria).
* `ToolParameter`: Nombre, tipo primitivo (`string`, `int`, `float`, `bool`), descripción, si es obligatorio y valor por defecto.
* `ToolDefinition`: Metadatos declarativos de la herramienta (nombre, descripción, nivel de riesgo, catálogo de parámetros, flag `requires_approval`).
* `ToolRequest`: Solicitud tipada que incluye `tool_name`, `arguments`, `trace_id`, `user_id`, `session_id` y `hitl_approved`.
* `ToolResult`: Respuesta estructurada con `tool_name`, `status` (`"success"`, `"error"`, `"blocked"`), `output`, `error`, `duration_ms`, `risk_level` y `trace_id`.

#### 2. Herramientas Nativas a Desplegar
* **`calculator_safe` (Riesgo LOW):**
  * Evaluador matemático determinista basado en el Abstract Syntax Tree (`ast.parse`) de Python.
  * Soporta operadores aritméticos estándar (`+`, `-`, `*`, `/`, `//`, `%`, `**`) y funciones matemáticas seguras (`abs`, `round`, `min`, `max`, `sqrt`, `ceil`, `floor`).
  * **Prohibición absoluta:** Sin uso de `eval()` ni `exec()`.
* **`web_search_and_read` (Riesgo MED):**
  * Wrapper unificado sobre `PlaywrightBrowserTool` (o `FirecrawlTool` con fallback local).
  * Parámetros: `url` (validada contra SSRF) y `max_length`.
  * Timeout estricto de **5,000 ms** (5 segundos).
* **`system_command_mock` (Riesgo CRITICAL):**
  * Herramienta de control para verificar que la gobernanza bloquee operaciones de sistema si no cuentan con `hitl_approved=True`.

---

### B. Capa 3.b: Gobernanza de Acción (`ActionPolicyService`)
**Ubicación:** `src/cognitive_assistant/modules/c3_governance/policy.py`

Ninguna herramienta en Capa 8 puede ejecutarse directamente. Antes del despacho, `ActionPolicyService.evaluate_action(request, tool_def)` debe emitir un veredicto `ActionPolicyDecision`:

1. **Control de Registro:** Si la herramienta solicitada no existe en `ToolRegistry` -> `allowed = False`, `violation_type = "unauthorized_tool"`.
2. **Control Anti-SSRF:** Si algún parámetro contiene una URL (`url`, `link`, etc.), se somete a `validate_outbound_url()`:
   * Rechazo de loopback (`127.0.0.1`, `localhost`).
   * Rechazo de RFC 1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
   * Rechazo de metadatos de Cloud (`169.254.169.254`).
   * Si falla -> `allowed = False`, `risk_level = CRITICAL`, `violation_type = "ssrf_attempt"`.
3. **Control Anti-Inyección de Comandos:** Inspección de argumentos de texto contra patrones maliciosos (`rm -rf`, `; del`, `| bash`, comillas invertidas, subshells `$()`).
4. **Control de Human-in-the-Loop (HITL):** Si `risk_level == CRITICAL` o `requires_approval == True`, y `hitl_approved == False` -> `allowed = False`, `requires_hitl = True`, `violation_type = "hitl_required"`.

---

### C. Capa 5: Orquestación ReAct en LangGraph
**Ubicación:** `src/cognitive_assistant/modules/c4_executive/graph.py` y `state.py`

#### 1. Extensión de `CognitiveState`
```python
class CognitiveState(TypedDict):
    # Campos preexistentes:
    input_message: str
    session_id: str
    user_id: str
    trace_id: str
    dialogue_history: List[Dict[str, Any]]
    active_goal: Optional[str]
    retrieved_memories: List[Dict[str, Any]]
    plan: List[str]
    response: str
    status: str
    metadata: Dict[str, Any]
    sensitive_data_filtered: Optional[bool]
    filter_reason: Optional[str]
    # Nuevos campos Fase 4:
    pending_tool_calls: Optional[List[Dict[str, Any]]]
    tool_results: Optional[List[Dict[str, Any]]]
```

#### 2. Reestructuración del Grafo
```text
[START]
   │
   ▼
[retrieve_memories] (Carga Working Memory de Redis y semántica de Mem0)
   │
   ▼
[deliberate_and_plan] (Evalúa si requiere tools -> genera pending_tool_calls)
   │
   ├─ ¿Tiene pending_tool_calls?
   │      ├── Sí ──> [execute_tools] ──┐ (Evalúa C3.b + Ejecuta en C8 Sandbox)
   │      └── No ─────────────────────┼──> [consolidate_memory] (Guarda en Redis y Mem0)
   │                                  │        │
   │                                  └────────┤
   │                                           ▼
                                            [END]
```

#### 3. Nodo `execute_tools_node`
* Itera los `pending_tool_calls`.
* Invoca `ActionPolicyService.evaluate_action()`.
* Si es denegado: genera `ToolResult(status="blocked")` y registra la infracción.
* Si es autorizado: ejecuta la función en el sandbox con medición de tiempo (`duration_ms`).
* Sintetiza los resultados en el campo `response` y actualiza el plan cognitivo con los pasos ejecutados.

---

### D. Optimización de Timeouts y Resiliencia Periférica
**Ubicación:** `src/cognitive_assistant/shared/tools/web_browser.py`

* Reducir `default_timeout_ms` de Playwright a **5,000 ms** (5 segundos).
* Envolver la navegación con captura limpia de excepciones para evitar que un fallo de red o un timeout no controlado interrumpa el ciclo del agente.

---

## 4. Matriz de Pruebas y Criterios de Aceptación (Definición de Terminado)

Para considerar la Fase 4 formalmente **CERRADA**, se deben crear y aprobar las siguientes suites:

| Archivo de Prueba | Casos a Verificar |
| :--- | :--- |
| `tests/test_tool_registry.py` | 1. Registro e introspección de herramientas.<br>2. Cálculo exitoso con `calculator_safe` (operaciones combinadas).<br>3. Manejo de división por cero y sintaxis inválida sin excepción no capturada.<br>4. Rechazo de herramienta inexistente. |
| `tests/test_governance_action.py` | 1. Bloqueo de peticiones con URLs privadas o de loopback (anti-SSRF en Capa 3.b).<br>2. Bloqueo de inyecciones de comandos en argumentos.<br>3. Bloqueo de herramientas CRITICAL sin flag `hitl_approved`.<br>4. Aprobación exitosa de herramientas LOW/MED con argumentos benignos. |
| `tests/test_react_cycle.py` | 1. Ciclo de deliberación sin herramientas (flujo directo a consolidación).<br>2. Ciclo deliberativo con llamada a `calculator_safe` (bifurcación a `execute_tools` y síntesis en respuesta).<br>3. Persistencia auditada del resultado de la herramienta en `working_memory`. |

**Meta de Suite Completa:** `>= 50 tests en verde` (46 preexistentes + mínimo 4-6 nuevos tests de Fase 4) con 0 fallos y 0 regresiones.

---

## 5. Checklist de Ejecución Paso a Paso

- [ ] **Paso 1:** Finalizar y guardar [`src/cognitive_assistant/shared/tools/registry.py`](file:///c:/Users/moise/OneDrive/Desktop/cognitive-assistant/src/cognitive_assistant/shared/tools/registry.py).
- [ ] **Paso 2:** Finalizar y guardar [`src/cognitive_assistant/modules/c3_governance/policy.py`](file:///c:/Users/moise/OneDrive/Desktop/cognitive-assistant/src/cognitive_assistant/modules/c3_governance/policy.py) y su export en `__init__.py`.
- [ ] **Paso 3:** Conectar y compilar el grafo LangGraph con bifurcación condicional en [`src/cognitive_assistant/modules/c4_executive/graph.py`](file:///c:/Users/moise/OneDrive/Desktop/cognitive-assistant/src/cognitive_assistant/modules/c4_executive/graph.py).
- [ ] **Paso 4:** Reducir timeout en [`src/cognitive_assistant/shared/tools/web_browser.py`](file:///c:/Users/moise/OneDrive/Desktop/cognitive-assistant/src/cognitive_assistant/shared/tools/web_browser.py) a 5000 ms.
- [ ] **Paso 5:** Implementar `tests/test_tool_registry.py` y `tests/test_react_cycle.py`.
- [ ] **Paso 6:** Ejecutar `pytest -q` y verificar que la suite completa pase al 100%.
- [ ] **Paso 7:** Generar commit único de cierre de Fase 4: `feat(react): integracion de ToolRegistry, gobernanza de accion Capa 3.b y ciclo ReAct en LangGraph`.
