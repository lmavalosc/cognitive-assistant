# ADR 001: Adopción de Monolito Modular Hexagonal

## Estado
Aceptado

## Contexto
El sistema cognitivo requiere desacoplar 8 capas funcionales complejas sin incurrir en la sobrecarga operacional, latencia de red innecesaria y complejidad de despliegue distribuido de los microservicios en una etapa de investigación de tesis.

## Decisión
Adoptar una arquitectura de **Monolito Modular Hexagonal** en Python:
- Un solo artefacto desplegable con límites de módulos estrictos (`c1_perception` a `c8_effectors`).
- Núcleo compartido (`shared/`) con contratos Pydantic inmutables, eventos de dominio y jerarquía de errores.
- Puertos y adaptadores en `platform/` para desacoplar el dominio de la infraestructura (Postgres, Redis, LLMs, Docker SDK).

## Consecuencias
- **Positivas:** Pruebas unitarias e integradas simplificadas en un único proceso, llamadas sincrónicas de bajísima latencia entre módulos, consistencia de tipos.
- **Negativas:** Requiere disciplina para evitar acoplamientos circulares entre módulos vecinos sin pasar por los contratos de `shared/`.
