# Arquitectura Objetivo del Sistema: 10 Capas Funcionales y 2 Planos Transversales
## Asistente Cognitivo Modular (JARVIS 0.0) — Taxonomía Canon v2.0
**Documento:** `TR-COG-2026-ARCH-V2.1`
**Fecha de entrada en vigencia:** 08 de Octubre, 2026
**Estado:** VIGENTE — Reemplaza a `DATA/arquitectura_8_capas.md` (v1.0, conservado como referencia histórica)
**Decisión formal:** ver `DATA/adr/007_evolucion_8_a_10_capas.md`

---

## 1. Regla constitutiva: por qué existen exactamente 10 capas

Una capa solo existe si pasa el **test de irreducibilidad** con tres preguntas:

1. **Función:** ¿qué hace que ninguna otra capa puede absorber sin convertirse en una "capa dios"?
2. **Datos:** ¿de qué datos es dueña exclusiva?
3. **Fallo:** ¿qué modo de fallo solo ella puede contener?

El número 10 no es aspiracional ni cosmético: es el resultado del test. Más capas que escenarios experimentales capaces de validarlas (7) serían inflación arquitectónica; menos capas reproduce el error de la "capa dios" detectado en la v1.0 (antigua Capa 4 con cuatro responsabilidades).

---

## 2. Mapa de las 10 Capas

```
                      +------------------------+
                      |   USUARIO / ENTORNO    |
                      +------------------------+
                                |    ^
             Estímulo crudo     |    |   Respuesta / Acción + trace_id
                                v    |
+--------------------------------------------------------------------------------+
| CAPA 1: PERCEPCIÓN MULTICANAL                                                  |
| (HTTP, Telegram, audio/Whisper, webhooks; transducción a PerceptionEvent)      |
+--------------------------------------------------------------------------------+
                                |
                                v
+--------------------------------------------------------------------------------+
| CAPA 2: RECEPCIÓN SEGURA Y NORMALIZACIÓN                                       |
| (Contratos Pydantic, trace_id, rate limiting, errores RFC 7807, auth de API)   |
+--------------------------------------------------------------------------------+
                                |
                                v
+--------------------------------------------------------------------------------+
| CAPA 3: GOBERNANZA E INMUNIDAD COGNITIVA  — 3 PUNTOS DE CONTROL                |
|  (a) Entrada: PromptGuard, sanitización, clasificación de riesgo               |
|  (b) Acción:  policy check sobre cada ToolRequest (LOW/MED/HIGH/CRITICAL+HITL) |
|  (c) Salida:  filtro de fuga de secretos/PII en la respuesta y en la memoria   |
+--------------------------------------------------------------------------------+
                    | (Aprobado)            | (Rechazado -> 403 RFC 7807 + auditoría)
                    v
+--------------------------------------------------------------------------------+
| CAPA 4: MEMORIA DE TRABAJO Y FOCO ATENCIONAL                                   |
| (Redis; ventana deslizante, active_goal, resumen rodante; latencia < 20 ms)    |
+--------------------------------------------------------------------------------+
                    |
                    v
+--------------------------------------------------------------------------------+
| CAPA 5: EJECUTIVO COGNITIVO Y PLANIFICACIÓN METACOGNITIVA                      |
| (LangGraph; CognitivePlan acíclico, confidence_score, clarificación,           |
|  decisión de uso de herramientas)                                              |
+--------------------------------------------------------------------------------+
        ^                    |                             |
        | (contexto RAG)     v (subtareas)                 v (ToolRequest -> pasa por
+----------------------------+      +------------------------------+  Capa 3.b)
| CAPA 6: MEMORIAS          |      | CAPA 7: AGENTES ESPECIALIZADOS |
| PERSISTENTES (Hipocampo)  |      | (Investigador, Programador,   |
| Episódica SQL + Semántica |      |  Verificador/Crítico)         |
| pgvector + Perfil Usuario |      +------------------------------+
+----------------------------+                     |
                                                   v
                              +---------------------------------------------+
                              | CAPA 8: EJECUCIÓN CONFINADA DE HERRAMIENTAS |
                              | (Sandbox Docker, MCP, timeout 15s, recursos |
                              |  limitados; LATENTE hasta cerrar gobernanza)|
                              +---------------------------------------------+
                                                   | (ToolResult)
                                                   v
+--------------------------------------------------------------------------------+
| CAPA 10: EFECTORES, RESPUESTA Y OBSERVACIÓN DE CONSECUENCIAS                   |
| (Salida al usuario/entorno + OutcomeEvent registra efecto real; cierra         |
|  episodio hacia Capa 6)                                                        |
+--------------------------------------------------------------------------------+
        |                                                     |
        | episodios cerrados                                  | batch nocturno
        v                                                     v
+--------------------------------------------------------------------------------+
| CAPA 9: APRENDIZAJE OFFLINE Y HOMEOSTASIS                                      |
| (Consolidación batch, actualización de UserProfile, políticas de olvido y      |
|  decaimiento; se ejecuta fuera del ciclo síncrono)                             |
+--------------------------------------------------------------------------------+

PLANO A (transversal): Infraestructura — LLM Gateway (LiteLLM), PostgreSQL, Redis.
PLANO B (transversal): Observabilidad y Auditoría — trace_id universal, logs JSON,
                       OpenTelemetry, tabla audit_transactions.
```

Nota de orden: la Capa 9 se dibuja al final del grafo pero opera asíncronamente sobre los artefactos de todo el ciclo; su posición numérica (9) es anterior a la de Efectores (10) porque el aprendizaje actúa **sobre** el sistema, no **hacia** el entorno. Los Planos A y B no se numeran: son servicios transversales sin función cognitiva propia.

---

## 3. Equivalencia: taxonomía v1.0 (8 capas + 3 planos) -> v2.1 (10 capas + 2 planos)

| v1.0 (histórica) | v2.1 (vigente) | Justificación del cambio |
|---|---|---|
| Capa 1 Percepción y Atención | **Capa 1 Percepción Multicanal** | Sin cambio estructural. La evaluación de saliencia se apoya en Capa 4 (foco), no la contradice. |
| Capa 2 Recepción | **Capa 2 Recepción Segura** | Se añade como responsabilidad explícita la autenticación de API (P0 de la auditoría de seguridad). |
| Capa 3 Gobernanza | **Capa 3 Gobernanza e Inmunidad** | Se amplía de filtro de entrada a **tres puntos de control** (entrada, acción sobre herramientas, salida). |
| Capa 4 Ejecutivo + Memoria de Trabajo | **Capa 4 (Memoria de Trabajo)** + **Capa 5 (Ejecutivo)** | División por test de irreducibilidad: datos, latencia y modo de fallo distintos. Resuelve la "capa dios" de v1.0. |
| Capa 5 Memorias Persistentes | **Capa 6 Memorias Persistentes** | Renumeración; sin cambio funcional. |
| Capa 6 Agentes Especializados | **Capa 7 Agentes Especializados** | Renumeración; sin cambio funcional. |
| Capa 7 Sandbox de Herramientas | **Capa 8 Ejecución Confinada** | Renumeración; sin cambio funcional. |
| (no existía como capa) | **Capa 9 Aprendizaje Offline y Homeostasis** | Plano C de v1.0 promovido a capa: tiene ciclo de vida, datos propios (UserProfile) y escenario de validación propio (Escenario 6). |
| Capa 8 Efectores | **Capa 10 Efectores y Observación de Consecuencias** | Se formaliza el `OutcomeEvent` (registro del efecto real) como contrato obligatorio para afirmar "ciclo cerrado" en la tesis. |
| Plano A Infraestructura | **Plano A** | Sin cambio. |
| Plano B Observabilidad/Auditoría | **Plano B** | Sin cambio. |
| Plano C Aprendizaje | (absorbido por Capa 9) | Promovido; deja de ser plano. |

---

## 4. Estado real de implementación al 08-10-2026

| Capa v2.1 | Estado | Evidencia en código |
|---|---|---|
| C1 Percepción | Parcial (herramientas web existen; Telegram/audio pendientes) | `shared/tools/web_browser.py` |
| C2 Recepción | Operativo con brechas P0 (sin auth, sin rate limit) | `modules/c2_reception/` |
| C3 Gobernanza | **No implementada** — bloqueo P0 antes de herramientas | (plan: Fase 3, `AUDITORIA&REPARACIÓN/PROMPT_REMEDIACION_SEGURIDAD.md`) |
| C4 Memoria de Trabajo | Operativo (Redis, 6 turnos, TTL 24h) | `modules/c4_executive/working_memory.py` |
| C5 Ejecutivo | Operativo básico (grafo lineal de 3 nodos; planner acíclico pendiente) | `modules/c4_executive/graph.py` |
| C6 Memorias Persistentes | Parcial (Mem0 + fallback local; pgvector RAG pendiente) | `modules/c5_memory/` |
| C7 Agentes | No implementada | (Semana 4 del plan) |
| C8 Sandbox Herramientas | **Latente — no construir hasta cerrar C3** | (Semana 6 del plan) |
| C9 Aprendizaje Offline | No implementada | (Semana 8 del plan) |
| C10 Efectores + OutcomeEvent | Parcial (dispatcher existe; OutcomeEvent ausente) | `modules/c8_effectors/dispatcher.py` |

**Convención de nombres en código:** los módulos existentes mantienen sus nombres actuales (`c2_reception`, `c4_executive`, `c5_memory`, `c8_effectors`) hasta que una refactorización formal los migre. La numeración v2.1 es taxonomía de arquitectura y documentación; el código evolucionará por alias/wrappers, nunca por renombrado destructivo.

---

## 5. Aristas de retorno obligatorias (corrección estructural respecto a v1.0)

La v1.0 dibujaba una cascada. La v2.1 exige estos bucles documentados y, con el tiempo, implementados:

1. **C1 <-> C4:** la saliencia de un estímulo se evalúa contra el foco/objetivo activo.
2. **C5 <-> C6:** recuperación de contexto RAG y escritura de episodios.
3. **C3.b entre C7 y C8:** ningún ToolRequest se ejecuta sin policy check.
4. **C10 -> C6:** todo `OutcomeEvent` cierra el episodio en memoria persistente.
5. **C10 -> C9:** los episodios cerrados alimentan la consolidación batch.
6. **C3.c sobre la salida de C5/C10:** filtro de fuga antes de responder o persistir.
