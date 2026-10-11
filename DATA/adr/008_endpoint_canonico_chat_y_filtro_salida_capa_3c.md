# ADR 008: Endpoint Canónico /api/v1/chat, Filtro de Salida Capa 3.c y Proveedor Gemini

## Estado
Aceptado — 11 de Octubre, 2026

## Contexto

En el marco del cierre de la Fase 4 (Sandbox, Gobernanza de Acción y Ciclo ReAct en LangGraph) y la transición hacia la Fase 5, se identificaron tres necesidades arquitectónicas críticas:

1. **Deuda Técnica de Entrada (Dispersión de Endpoints):** El cliente HTTP invocaba `/reception/deliberate` o `/reception/message`, nombres acoplados a la jerga interna de recepción en lugar de seguir las convenciones canónicas de APIs conversacionales (`POST /api/v1/chat`). Faltaba un contrato unificado y fuertemente tipado para peticiones multi-turno.
2. **Proveedor LLM Definitivo en Plano A:** El sistema mantenía referencias de prueba a `gpt-4o-mini` como default. La estrategia de infraestructura del proyecto establece el uso prioritario de **Gemini API** (`gemini-2.5-flash`) servido a través de LiteLLM Gateway, permitiendo inferencias ultrarrápidas, menor latencia y observabilidad estandarizada sin perder el desacoplamiento multimodelo.
3. **Gobernanza de Salida Faltante (Capa 3.c):** La Capa 3 contaba con inspección de entrada (3.a: `PromptGuard`, sanitización PII e inyecciones) y gobernanza de acción (3.b: `ActionPolicyService`, validación de herramientas, SSRF y anti-spoofing HITL). Sin embargo, carecía del perimetro de salida (3.c), dejando expuesto al sistema a que una respuesta generada por el LLM o resultante de una herramienta pudiera exfiltrar secretos del sistema, claves de API (`AIzaSy...`, `sk-...`), cadenas de conexión a bases de datos con credenciales, tokens Bearer o datos confidenciales.

## Decisión

1. **Unificación Canónica en `POST /api/v1/chat`:**
   - Se establecen los esquemas Pydantic `ChatRequest` y `ChatResponse` en `src/cognitive_assistant/modules/c2_reception/schemas.py`.
   - Se implementa el endpoint `POST /api/v1/chat` en `src/cognitive_assistant/modules/c2_reception/router.py`.
   - Se preserva el alias `/reception/deliberate` apuntando al mismo pipeline para garantizar retrocompatibilidad total sin romper clientes existentes.

2. **Integración de Gemini API en LLMGateway (Plano A):**
   - Se configura `default_llm_model = "gemini/gemini-2.5-flash"` en `settings.py` y `.env.example`.
   - Se añade la propiedad `gemini_api_key` en `Settings`.
   - En `src/cognitive_assistant/shared/infrastructure/llm.py`, `LLMGateway` resuelve dinámicamente la clave correspondiente (`settings.gemini_api_key` o `settings.llm_api_key`) cuando se invoca un modelo bajo el prefijo `gemini/`, manteniendo el modo `mock_fallback` trazable para ejecución aislada o de pruebas.

3. **Activación de Capa 3.c (`OutputGuard`):**
   - Se crea `src/cognitive_assistant/modules/c3_governance/output_guard.py` exponiendo la clase `OutputGuard.filter_response(text, trace_id)`.
   - Se implementa un motor de detección regex contra:
     - Google API Keys (`AIzaSy...`) $\to$ `[REDACTED_GOOGLE_API_KEY]`
     - OpenAI y Tokens genéricos (`sk-...`, `ghp-...`) $\to$ `[REDACTED_API_KEY]`
     - URIs de BD con contraseñas (`postgresql://user:pass@host`) $\to$ `[REDACTED_USER]:[REDACTED_PASS]@[REDACTED_HOST]`
     - Asignaciones explícitas de contraseñas (`password: ...`, `contraseña = ...`) $\to$ `password=[REDACTED_SECRET]`
     - Claves privadas PEM y tarjetas de crédito.
   - Si se detecta fuga, se loguea advertencia de seguridad con el `trace_id`, se ofusca el contenido de forma no destructiva y se marca la transacción en auditoría (`security_violation=True`).

## Consecuencias

**Positivas:**
- Interfaz de entrada estandarizada según la especificación OpenAPI de la industria (`/api/v1/chat`).
- Cumplimiento estricto de la triple barrera de seguridad de Capa 3 (3.a Entrada, 3.b Acción, 3.c Salida).
- Arquitectura desacoplada en inferencia: Gemini como motor nativo de alta velocidad, con fallback simulado determinista cuando no hay red externa.
- 47 pruebas automatizadas validando la no regresión y la efectividad del filtro perimétrico.

**Negativas / Mitigaciones:**
- La evaluación de expresiones regulares en la salida añade una latencia negligible (< 1ms para textos de hasta 8000 caracteres).
