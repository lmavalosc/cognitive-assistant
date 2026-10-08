# ADR 005: OpenTelemetry y Traza Universal trace_id para Auditoría Inmutable

## Estado
Aceptado

## Contexto
El flujo cognitivo involucra múltiples capas, evaluación de políticas, llamadas LLM, consultas vectoriales y ejecución de herramientas. Diagnosticar anomalías o reconstruir la cadena de razonamiento requiere observabilidad completa de extremo a extremo.

## Decisión
Implementar instrumentación unificada con **OpenTelemetry** e inyección de un `trace_id` universal (UUIDv4) desde la Capa 2:
- El `trace_id` se propaga a través de `contextvars` en Python para asociar todos los logs, spans y registros en base de datos.
- Se retorna el header `X-Trace-ID` en cada respuesta HTTP.
- Cada decisión de gobernanza (Capa 3), ejecución de herramienta (Capa 7) y cierre de episodio (Capa 8) se persiste en una tabla inmutable de auditoría indexada por `trace_id`.

## Consecuencias
- **Positivas:** 100% de trazabilidad forense, diagnóstico simplificado en producción y validación empírica directa del Escenario 7 de la tesis.
- **Negativas:** Ligero costo de cómputo en la serialización de spans y persistencia sincrónica/asincrónica de logs de auditoría.
