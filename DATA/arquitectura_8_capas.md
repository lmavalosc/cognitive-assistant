# Arquitectura del Sistema: 8 Capas Funcionales y 3 Planos Transversales

> **⚠️ ESTADO: DOCUMENTO HISTÓRICO (v1.0) — REEMPLAZADO EL 08-10-2026**
>
> La taxonomía vigente es **10 Capas Funcionales + 2 Planos Transversales**:
> ver [`arquitectura_10_capas.md`](./arquitectura_10_capas.md) (documento canon v2.1)
> y [`adr/007_evolucion_8_a_10_capas.md`](./adr/007_evolucion_8_a_10_capas.md).
>
> Este archivo se conserva sin cambios de contenido como registro del diseño original.
> Defectos estructurales detectados en esta versión: (1) Capa 4 con cuatro
> responsabilidades simultáneas ("capa dios"), (2) Plano C era una capa funcional
> disfrazada de transversal, (3) gobernanza de un solo punto (solo entrada),
> (4) cascada lineal sin bucles de retroalimentación documentados.

## 1. Visión de la Taxonomía

El sistema organiza el procesamiento cognitivo en una secuencia determinista de 8 capas funcionales asistidas transversalmente por 3 planos de sustrato y auditoría.

```
                   +------------------------+
                   |   USUARIO / ENTORNO    |
                   +------------------------+
                             |    ^
              Estímulo Crudo |    | Efecto / Respuesta
                             v    |
+------------------------------------------------------------------------------+
| CAPA 1: PERCEPCIÓN SENSORIAL Y ATENCIÓN (Ingesta, Saliencia, Relevancia)     |
+------------------------------------------------------------------------------+
                             |
                             v
+------------------------------------------------------------------------------+
| CAPA 2: RECEPCIÓN SEGURA Y NORMALIZACIÓN (Gateway, Trace ID, Autenticación)  |
+------------------------------------------------------------------------------+
                             |
                             v
+------------------------------------------------------------------------------+
| CAPA 3: GOBERNANZA, IDENTIDAD Y VALORACIÓN (Políticas, RBAC, Control Riesgo) |
+------------------------------------------------------------------------------+
                 | (Aprobado)              | (Rechazado / Requiere Conf.)
                 v                         +---------------+
+-------------------------------------------------------+  |
| CAPA 4: EJECUTIVO COGNITIVO Y MEMORIA DE TRABAJO      |  |
| (Planner, Metacognición, Estado Mental en Redis)      |  |
+-------------------------------------------------------+  |
         ^                                                 |
         | (Recuperación / Contexto RAG)                   |
         v                                                 |
+-------------------------------------------------------+  |
| CAPA 5: MEMORIAS PERSISTENTES Y MODELO CONTEXTUAL     |  |
| (Episódica SQL, Semántica pgvector, Usuario, Mundo)   |  |
+-------------------------------------------------------+  |
         |                                                 |
         v (Tareas Asignadas)                              |
+-------------------------------------------------------+  |
| CAPA 6: AGENTES ESPECIALIZADOS Y ORQUESTACIÓN         |  |
| (Investigador, Programador, Domótico, Verificador)    |  |
+-------------------------------------------------------+  |
         |                                                 |
         v (ToolRequests)                                  |
+-------------------------------------------------------+  |
| CAPA 7: EJECUCIÓN SEGURA DE HERRAMIENTAS (SANDBOX)    |  |
| (Protocolo MCP, Docker Confinado, Timeouts, Límites)  |  |
+-------------------------------------------------------+  |
         |                                                 |
         v (ToolResults)                                   |
+------------------------------------------------------------------------------+
| CAPA 8: EFECTORES, RESPUESTA Y OBSERVACIÓN (Salida, Registro de Consecuencias)<--+
+------------------------------------------------------------------------------+
         |                                |
         | Despacho Externo               | Registro de Episodio Cerrado
         v                                v
+------------------------+      +----------------------------------------------+
|   USUARIO / ENTORNO    |      | Registra Episodio -> CAPA 5 (Memoria)        |
+------------------------+      +----------------------------------------------+
                                                  |
                                                  v Lote Batch Asíncrono
                                        [PLANO C: APRENDIZAJE]
```

---

## 2. Definición Detallada de las Capas

### Capa 1: Percepción Sensorial y Atención
- **Responsabilidad:** Ingesta multicanal (HTTP, Webhooks, Audio) y evaluación temprana de saliencia cognitiva.
- **Salida:** `AttentionResult` (intención, urgencia, relevancia, señal afectiva).

### Capa 2: Recepción Segura y Normalización
- **Responsabilidad:** Gateway perimetral, validación formal de esquemas, control de tasa (Token Bucket) y generación de `trace_id` universal.

### Capa 3: Gobernanza, Identidad y Valoración Contextual
- **Responsabilidad:** Motor de políticas deterministas (RBAC/ABAC), detección de Prompt Injection y compuerta Human-in-the-Loop (`NEEDS_CONFIRMATION`).

### Capa 4: Ejecutivo Cognitivo y Memoria de Trabajo
- **Responsabilidad:** Formulación del `CognitivePlan` acíclico, mantenimiento del estado activo en Redis y evaluación metacognitiva de confianza.

### Capa 5: Memorias Persistentes y Modelo Contextual
- **Responsabilidad:** Almacenamiento persistente: Memoria Episódica (PostgreSQL), Memoria Semántica (pgvector HNSW), Perfil del Usuario y Modelo del Mundo.

### Capa 6: Agentes Especializados y Orquestación
- **Responsabilidad:** Ejecución de subtareas mediante roles específicos (Investigador RAG, Programador, Verificador/Crítico).

### Capa 7: Ejecución Confinada de Herramientas (Sandbox)
- **Responsabilidad:** Aislamiento estricto de herramientas mediante Docker SDK efímero, sin acceso a red host, con topes de memoria (256MB) y timeout de 15s.

### Capa 8: Efectores, Respuesta y Observación de Consecuencias
- **Responsabilidad:** Despacho de la respuesta final al usuario/entorno, medición de telemetría de cierre y serialización del episodio completado hacia Capa 5.

---

## 3. Planos Transversales

### Plano A: Infraestructura y Modelos
Abstracción de inferencia LLM (Ollama / proveedores externos), conexiones a PostgreSQL y Redis.

### Plano B: Observabilidad y Auditoría
Propagación de `trace_id`, logging estructurado en JSON con sanitización PII, e instrumentación OpenTelemetry.

### Plano C: Aprendizaje Offline y Consolidación
Jobs programados en segundo plano para procesar episodios del día, extraer preferencias y actualizar perfiles de usuario.
