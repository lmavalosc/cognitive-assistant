# Anteproyecto de Grado: Asistente Cognitivo Modular Hexagonal

## 1. Título del Proyecto
**Diseño e Implementación de una Arquitectura Cognitiva Modular Hexagonal para Asistentes Inteligentes Basada en Ciclo Cognitivo Cerrado, Memorias Multinivel y Confinamiento de Herramientas.**

## 2. Definición del Problema
Los sistemas conversacionales basados en Modelos de Lenguaje Grandes (LLMs) típicamente sufren de:
- **Estructura reactiva lineal unidireccional**: Procesan cada entrada sin un ciclo cognitivo cerrado que verifique consecuencias empíricas.
- **Amnesia transaccional y sobrecarga de ventana de contexto**: Falta de separación formal entre la memoria de trabajo volátil (alta velocidad) y almacenes episódicos/semánticos de largo plazo.
- **Vulnerabilidades de seguridad en el uso de herramientas**: Riesgo de Prompt Injection, escalado de privilegios y ejecución descontrolada sobre el sistema anfitrión.
- **Opacidad operacional**: Dificultad para correlacionar decisiones internas de múltiples agentes en flujos heterogéneos.
- **Incapacidad de evolución offline**: Incapacidad de aprender o adaptar preferencias sin reentrenar pesos neuronales costosos.

## 3. Objetivos

### Objetivo General
Desarrollar una arquitectura de software basada en un monolito modular hexagonal en Python que implemente un asistente cognitivo persistente, seguro, observable y con aprendizaje continuo offline.

### Objetivos Específicos
1. Formalizar un ciclo cognitivo cerrado estructurado en 8 capas funcionales verticales y 3 planos transversales.
2. Implementar una memoria de trabajo volátil indexada en Redis y memorias persistentes (episódica relacional y semántica HNSW con pgvector) en PostgreSQL.
3. Incorporar un motor de gobernanza determinista con mitigación de Prompt Injection y protocolo Human-in-the-Loop.
4. Confinar la ejecución de herramientas generadas por agentes mediante contenedores efímeros Docker SDK con límites estrictos de recursos y tiempo.
5. Garantizar observabilidad de día cero mediante propagación universal de `trace_id` con OpenTelemetry.
6. Habilitar consolidación offline y mutación dinámica de perfiles de usuario mediante procesamiento asíncrono batch.
7. Evaluar empíricamente el sistema a través de 7 escenarios experimentales rigurosos.

## 4. Metodología
Se adopta la estrategia constructiva **"Core-to-Periphery"** (del núcleo a la periferia) dividida en 8 etapas secuenciales donde cada iteración produce un sistema completamente ejecutable, verificable y testeable de extremo a extremo.

---

## 5. Addendum de Precisión Taxonómica (08-10-2026)

El Objetivo Específico 1 menciona "8 capas funcionales verticales y 3 planos transversales", correspondiente a la taxonomía inicial del diseño (v1.0). Durante la ejecución del Tronco Encefálico, la auditoría arquitectónica detectó defectos estructurales en esa numeración (capa con responsabilidades múltiples, plano transversal que era funcionalmente una capa, gobernanza de un solo punto, ausencia de bucles de retroalimentación documentados).

Por **ADR 007** (`DATA/adr/007_evolucion_8_a_10_capas.md`), la arquitectura objetivo se formaliza como **10 capas funcionales + 2 planos transversales** (`DATA/arquitectura_10_capas.md`). Esta evolución no altera el Objetivo General, la metodología Core-to-Periphery ni los 7 escenarios experimentales: es una especialización de la misma propuesta, derivada de la evidencia de implementación. Si el documento formal del anteproyecto ya fue radicado ante el comité, esta sección sirve como nota de precisión para la sustentación; si aún no se radica, el Objetivo 1 puede reeditarse textualmente a "10 capas funcionales verticales y 2 planos transversales".
