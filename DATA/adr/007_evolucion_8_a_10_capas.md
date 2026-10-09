# ADR 007: Evolución de la Taxonomía de 8 Capas + 3 Planos a 10 Capas + 2 Planos

## Estado
Aceptado — 08 de Octubre, 2026

## Contexto

La taxonomía v1.0 (`DATA/arquitectura_8_capas.md`) definía 8 capas funcionales y 3 planos transversales. La auditoría arquitectónica realizada el 08-10-2026, contrastando el diseño con el código construido en los Días 1 y 2, detectó cuatro defectos estructurales:

1. **Capa dios:** la antigua Capa 4 acumulaba memoria de trabajo, planner, metacognición y orquestación — cuatro responsabilidades con modelos de datos, latencias y modos de fallo incompatibles.
2. **Plano disfrazado:** el Plano C (aprendizaje offline) tenía ciclo de vida, datos propios (`UserProfile`) y un escenario experimental propio (Escenario 6); era una capa funcional clasificada como transversal, contradicción taxonómica.
3. **Gobernanza de un solo punto:** la antigua Capa 3 era solo filtro de entrada; la seguridad real exige control también sobre cada ToolRequest (acción) y sobre la respuesta (salida), como confirmó la auditoría de seguridad (`DATA/AUDITORIA&REPARACIÓN/AUDITORIA_SEGURIDAD_2026-10-08.md`, SEC-06/09/10/19).
4. **Cascada sin retorno:** el diagrama v1.0 no especificaba los bucles de retroalimentación (atención↔foco, consecuencia→memoria) que el anteproyecto promete al hablar de "ciclo cognitivo cerrado".

Se aplica además la regla de evidencia: el número máximo de capas defendibles es el que los 7 escenarios experimentales del plan maestro pueden validar empíricamente en 8 semanas.

## Decisión

Adoptar como arquitectura objetivo **10 capas funcionales + 2 planos transversales**, formalizada en `DATA/arquitectura_10_capas.md` (v2.1):

1. División de la antigua Capa 4 en **Capa 4 (Memoria de Trabajo / foco atencional, Redis)** y **Capa 5 (Ejecutivo cognitivo y planner metacognitivo, LangGraph)**.
2. Promoción del antiguo Plano C a **Capa 9 (Aprendizaje Offline y Homeostasis)**.
3. Renumeración de memorias persistentes (Capa 6), agentes (Capa 7), sandbox (Capa 8) y efectores (Capa 10, con contrato `OutcomeEvent` obligatorio).
4. **Capa 3** redefinida con tres puntos de control: entrada (pre-LLM), acción (pre-herramienta) y salida (post-LLM).
5. Planos transversales reducidos a dos: **Plano A (Infraestructura)** y **Plano B (Observabilidad y Auditoría)**.
6. Cada capa queda justificada por el test de irreducibilidad: función exclusiva, datos propios y modo de fallo propio.
7. **Compatibilidad de código:** los módulos existentes (`c2_reception`, `c4_executive`, `c5_memory`, `c8_effectors`) conservan su nombre; la migración a la nueva numeración se hará por alias/wrappers, nunca por renombrado destructivo, y se documentará en el informe que corresponda.
8. Esta decisión deja sin effecto retroactivo a los informes de los Días 1 y 2 (registros históricos), que se corrigen mediante secciones de errata, no reescritura.

Se reserva el número **ADR 006** para la decisión de implementación del cortafuegos cognitivo (Capa 3), que documentará la remediación P0/P1 iniciada con `DATA/AUDITORIA&REPARACIÓN/PROMPT_REMEDIACION_SEGURIDAD.md`.

## Consecuencias

**Positivas:**
- La tesis tiene una taxonomía defendible pregunta a pregunta (irreducibilidad por capa).
- El Plan maestro, la arquitectura y el código vuelven a ser coherentes entre sí.
- La Cadena de seguridad correcta queda explícita: Gobernanza (C3) -> Sandbox (C8) -> Herramientas autónomas, bloqueando la Fase 4 hasta cerrar los P0.
- La promoción del aprendizaje a Capa 9 alinea el diagrama con el Escenario 6.

**Negativas:**
- Todos los planes e informes previos requieren errata/actualización (ejecutada el 08-10-2026).
- Los nombres de módulos actuales no coincidirán temporalmente con la numeración taxonómica; riesgo mitigado por la convención de alias y por la tabla de equivalencia del documento canon.

**Referencias:** `DATA/arquitectura_10_capas.md` (vigente), `DATA/arquitectura_8_capas.md` (histórico), `DATA/AUDITORIA&REPARACIÓN/AUDITORIA_SEGURIDAD_2026-10-08.md`, `DATA/plan_de_trabajo/PLAN_DE_TRABAJO_8_SEMANAS.md` (actualizado).
