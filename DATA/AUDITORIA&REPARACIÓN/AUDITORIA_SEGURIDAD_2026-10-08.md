# AUDITORÍA DE SEGURIDAD — ESTADO ACTUAL DEL CÓDIGO
## Proyecto: Asistente Cognitivo Modular (JARVIS 0.0)
**Documento:** `TR-COG-2026-SEC-AUDIT-01`
**Fecha:** 08 de Octubre, 2026
**Rama auditada:** `semana1-tronco-encefalico` (HEAD `898de24` + cambios sin commitear)
**Método:** Revisión estática documento por documento, verificación de controles reales vs. plan maestro, análisis de vectores de ataque.
**Nota metodológica:** Esta auditoría verifica lo que el código **hace hoy**, no lo que los informes de avance **declaran**. Donde difieren, se marca como divergencia.

---

## 1. Veredicto Global de Seguridad

| Dimensión | Estado | Nota |
|---|---|---|
| Perímetro de red / exposición | ⚠️ Débil | API en `0.0.0.0:8000`, PostgreSQL en `5433`, Redis en `6379`, todos sin autenticación ni TLS. |
| Autenticación / Autorización de API | ❌ **Inexistente** | Ningún endpoint exige credenciales, tokens ni scopes. |
| Gobernanza cognitiva (Capa 3) | ❌ **No implementada** | Todo estímulo llega crudo al LLM. |
| Rate limiting | ❌ **Configurado pero no implementado** | `RATE_LIMIT_ENABLED=true` es decorativo: no existe middleware ni código que lo use (Día 05 de Semana 1 pendiente). |
| Gestión de secretos | ✅ Correcto | `.env` no está versionado (solo `.env.example`), `.gitignore` lo excluye, sin secretos hardcodeados en código. |
| Trazabilidad | ⚠️ Parcial | `trace_id` universal funciona, pero acepta trace_ids arbitrarios suministrados por el cliente sin validación. |
| Persistencia de auditoría | ⚠️ Parcial | `audit_transactions` funciona, pero el contenido del estímulo se guarda sin sanitización PII (hasta 1000 caracteres). |
| Ejecución de herramientas | ⚠️ Latente | SSRF no mitigado en Playwright/Firecrawl; hoy mitigado solo porque no están cableadas a ningún endpoint. |

**Postura de seguridad actual: 3.5 / 10** — aceptable para tronco encefálico en red local confiable; **inaceptable para cualquier exposición fuera de localhost** o para conectar un LLM real con herramientas. La brecha #1 y #2 deben cerrarse antes de la Fase 4 del Día 2.

---

## 2. Hallazgos por Documento / Archivo

### 2.1. `src/cognitive_assistant/settings.py` — ⚠️ 2 hallazgos

| ID | Severidad | Hallazgo | Evidencia | Corrección |
|---|---|---|---|---|
| SEC-01 | **Alta** | Credenciales por defecto débiles compiladas en el modelo de settings: `postgres_password: str = "nucleo"`. Si alguien despliega sin `.env`, el sistema arranca con la contraseña más adivinable posible. | `settings.py` líneas 12-15 | Sin defaults de password: `postgres_password: str = Field(..., env=...)`, fallar en arranque si falta en `app_env != "local"`. |
| SEC-02 | Media | `rate_limit_enabled/requests/window_seconds` definidos pero **ningún archivo del proyecto los consume**. Falsa sensación de control. | Grep de `rate_limit` en `src/`: solo aparece en settings. | Implementar middleware Token Bucket sobre Redis (Día 05, plan Semana 1) o eliminar la config hasta implementarlo. |

### 2.2. `src/cognitive_assistant/app.py` — ⚠️ 2 hallazgos

| ID | Severidad | Hallazgo | Evidencia | Corrección |
|---|---|---|---|---|
| SEC-03 | **Crítica** | **Sin CORS ni autenticación**: `create_app()` solo registra `TraceIDMiddleware` y los routers. No hay `CORSMiddleware` deliberado, ni dependencia de auth, ni red confiable. Cualquier proceso del host (o de la LAN, por `0.0.0.0`) puede invocar todo. | `app.py` completo | Añadir `CORSMiddleware` explícito (allowlist de orígenes) y dependencia de autenticación (API key / JWT) en routers no-públicos. |
| SEC-04 | Media | `lifespan` ejecuta `init_db_schema()` (con `CREATE EXTENSION`) al arrancar: la app necesita permisos de superusuario/DDL en PostgreSQL para siempre. Viola principio de mínimo privilegio. | `app.py` lifespan | Separar usuario de migraciones (DDL) del usuario de runtime (DML) — migraciones fuera del lifespan en despliegues serios. |

### 2.3. `src/cognitive_assistant/modules/c2_reception/router.py` — ❌ 4 hallazgos (el archivo más expuesto)

| ID | Severidad | Hallazgo | Evidencia | Corrección |
|---|---|---|---|---|
| SEC-05 | **Crítica** | **IDOR / sin aislamiento entre usuarios y sesiones**: `user_id` y `session_id` son autodeclarados por el cliente (`DeliberateRequest`), sin autenticación ni validación de propiedad. Cualquier llamante puede leer/envenenar la memoria de trabajo y la memoria persistente de cualquier usuario (`user_id="otro"`). | `router.py` + `schemas.py: DeliberateRequest` | Derivar `user_id` de una identidad autenticada, no del body. Validar propiedad de `session_id`. |
| SEC-06 | **Crítica** | **Prompt injection directo al LLM**: `content` pasa sin sanitización del endpoint al system prompt y mensajes de LangGraph (`execute_cognitive_cycle`). Capa 3 no existe hoy. Un atacante puede: (a) manipular deliberación, (b) sembrar memorias maliciosas en Mem0/Redis vía consolidación automática (`consolidate_memory_node`) — **inyección persistente de segundo orden** que afectará turnos futuros de cualquier sesión que recupere esos recuerdos. | `deliberate_message` → `graph.py` nodos 2 y 3 | Implementar `c3_governance` (PromptGuard + sanitizer + veredicto 403) ANTES de `execute_cognitive_cycle`, per plan Día 2 Fase 3. No invocar LLM ni `consolidate` si `allowed=False`. |
| SEC-07 | Alta | **Sin límite de longitud de entrada**: `content: str = Field(..., min_length=1)` sin `max_length`. El plan maestro fija 8000 chars. Payloads gigantes → coste LLM no acotado, llenado de Redis/DB, DoS por memoria. | `schemas.py: ReceptionMessageRequest.content`, `DeliberateRequest.content` | `Field(..., min_length=1, max_length=8000)` + sanitizador NFKC + rechazo de caracteres de control. |
| SEC-08 | Media | `request_summary=payload.content` se persiste en `audit_transactions` **sin sanitización de PII** ni truncado en el endpoint de recepción (AuditService trunca a 1000 en `record_transaction`, pero sin scrubbing). El plan de la Semana 1 exigía explícitamente "no guardes payloads completos si pueden contener datos sensibles". | `router.py` → `audit.py` | Aplicar scrubber PII (emails, tarjetas, DNI, claves) antes de persistir; considerar hash + extracto. |

### 2.4. `src/cognitive_assistant/modules/c2_reception/schemas.py` — cubierto por SEC-05/07

### 2.5. `src/cognitive_assistant/modules/c4_executive/graph.py` — ❌ 2 hallazgos

| ID | Severidad | Hallazgo | Evidencia | Corrección |
|---|---|---|---|---|
| SEC-09 | **Alta** | **Consolidación sin consentimiento ni filtrado**: `consolidate_memory_node` guarda TODO turno (usuario + respuesta) en Redis y Mem0, incluidos posibles secretos que el usuario pegue por error o que un inyector siembre. No hay clasificación de sensibilidad antes de persistir. | `graph.py` nodo consolidate | Añadir clasificador de sensibilidad previo a `memory_service.add`; no persistir si contiene patrones de secretos/PII sin flag explícita. |
| SEC-10 | Media | El system prompt interpolado con recuerdos (`f"Recuerdos persistentes del usuario:\n- {context_str}"`) permite que contenido de Mem0 se ejecute como instrucción (memoria como vector de ataque). | `graph.py` nodo deliberate | Delimitar recuerdos como datos (fences/estructura) y añadir instrucción anti-sobreescritura + citar que el LLM debe tratarlos como contenido, no instrucciones. |

### 2.6. `src/cognitive_assistant/modules/c4_executive/working_memory.py` — ⚠️ 1 hallazgo

| ID | Severidad | Hallazgo | Evidencia | Corrección |
|---|---|---|---|---|
| SEC-11 | Media | Claves Redis `session:{session_id}:working_memory` construidas con `session_id` arbitrario del cliente y sin namespace por usuario. Combinado con SEC-05: enumeración/escritura cruzada de sesiones y posible colisión deliberada. El TTL de 24h y fallback en RAM retienen contenido conversacional sin cifrado. | `working_memory.py` `_format_key` | Namespace `user:{user_id}:session:{session_id}:wm` tras autenticación; considerar cifrado at-rest de valores en Redis para producción. |

### 2.7. `src/cognitive_assistant/modules/c5_memory/service.py` + `router.py` — ❌ 2 hallazgos

| ID | Severidad | Hallazgo | Evidencia | Corrección |
|---|---|---|---|---|
| SEC-12 | **Crítica** | **Endpoints de memoria totalmente abiertos**: `POST /memory/add`, `GET /memory/search`, `GET /memory/all` permiten a cualquier llamante leer TODOS los recuerdos de TODOS los usuarios (`user_id` como query param) e inyectar recuerdos arbitrarios en perfiles ajenos (volverá al prompt vía SEC-10). Es exfiltración y envenenamiento por diseño en el estado actual. | `c5_memory/router.py` completo | Autenticación obligatoria + `user_id` derivado del principal autenticado; eliminar `user_id` como parámetro de entrada libre. |
| SEC-13 | Media | `MemoryService.reset(user_id)` existe en el servicio y hoy no está expuesto por HTTP; cualquier futura exposición sin confirmaación/HITL se convierte en borrado destructivo sin salvavidas. | `service.py: reset()` | Cuando se exponga: Capa 3 → acción `HIGH` → `NEEDS_CONFIRMATION` (plan Semana 5). |

### 2.8. `src/cognitive_assistant/shared/infrastructure/llm.py` — ⚠️ 2 hallazgos

| ID | Severidad | Hallazgo | Evidencia | Corrección |
|---|---|---|---|---|
| SEC-14 | Media | En fallo de LiteLLM con fallback activo, el mensaje de error del proveedor (`str(exc)`) se devuelve **al usuario dentro del contenido** (`"error": str(exc)`). Los errores de SDK suelen incluir fragmentos de config/headers/endpoints → fuga de información. | `llm.py` bloque except | Devolver error genérico al cliente; detalle completo solo en logs internos. |
| SEC-15 | Baja | `mock_fallback` retorna contenido "procesado con éxito" indistinguible estructuralmente de una respuesta real: un despliegue mal configurado responderá simulaciones en producción sin que el usuario lo note salvo por el texto. | `llm.py` bloque mock | Añadir flag observable (`"mock": true` en respuesta y log WARN) y desactivar fallback por defecto cuando `app_env != "local"`. |

### 2.9. `src/cognitive_assistant/shared/infrastructure/audit.py` + `models.py` — ⚠️ 1 hallazgo estructural

| ID | Severidad | Hallazgo | Evidencia | Corrección |
|---|---|---|---|---|
| SEC-16 | Media | La "inmutabilidad" de auditoría es solo programa-level: el mismo rol `nucleo` que usa la app puede `UPDATE/DELETE` en `audit_transactions`. Además el fallback a logs cuando la DB falla convierte la auditoría en eventual sin alarma. | `models.py`, `audit.py`, `docker-compose.yml` | Rol de solo INSERT para runtime; usuario DDL separado; métrica/alerta si `record_transaction` cae en fallback (Plano B). |

### 2.10. `src/cognitive_assistant/shared/telemetry/trace.py` + `logging.py` — ⚠️ 2 hallazgos

| ID | Severidad | Hallazgo | Evidencia | Corrección |
|---|---|---|---|---|
| SEC-17 | **Alta** | **Suplantación de trazas**: el middleware acepta `X-Trace-ID` del cliente sin validación (formato, longitud, prefijo). Un actor puede fijar trace_ids para colisionar auditorías de otras transacciones, envenenar búsquedas forenses, o inyectar caracteres de control que acaban en logs JSON y en la columna `String(64)` de auditoría (log injection). | `trace.py: dispatch` | Validar con regex `^[A-Za-z0-9-]{36}$` (o re-generar si no es UUIDv4 válido) y truncar a 64 chars; considerar marcar trazas externas con prefijo `ext-`. |
| SEC-18 | Baja | `TraceIdFilter.filter()` llama a `get_trace_id()`, que **genera** un trace_id si no hay contexto: los logs fuera de request contaminan el ContextVar con identificadores artificiales que pueden propagarse a ejecuciones internas (ruido forense, no vulnerabilidad directa). | `logging.py: TraceIdFilter` | Filtro debe solo leer; generación solo en middleware. |

### 2.11. `src/cognitive_assistant/shared/tools/web_browser.py` — ⚠️ 1 hallazgo latente

| ID | Severidad | Hallazgo | Evidencia | Corrección |
|---|---|---|---|---|
| SEC-19 | **Alta (latente)** | **SSRF abierto**: `fetch_page_content(url)` y `scrape_url(url)` no validan esquema (`file://`, `gopher:`) ni destino (localhost, RFC1918 `10.x/172.16.x/192.168.x`, metadata cloud `169.254.169.254`, IPv6 link-local). El plan del Día 2 ya lo anticipaba (Etapa 4.3: "rechazo de IPs privadas"). Hoy la mitigación real es que **la herramienta no está expuesta al grafo**. En el momento en que el nodo ReAct se cablee (Fase 4), esto se vuelve explotable remotamente vía prompt. | `web_browser.py: fetch_page_content`, plan Día 2 Etapa 4.3 | Antes de cablear herramientas a LangGraph: URL validator (esquema allowlist http/https, resolución DNS y rechazo de rangos privados/loopback), timeout 5s (ya planeado), y ejecución bajo sandbox Docker (Capa 7). |

### 2.12. `src/cognitive_assistant/shared/infrastructure/redis_client.py` — ✅ con nota

Controles presentes correctos: fallback en memoria, cierre limpio, reintento tras timeout, recreación en cambio de event loop. **Nota:** el fallback en RAM (SEC-adjunto a SEC-11) retiene conversaciones sin expiración efectiva si `ttl_seconds` se pasa como `None` — hoy `WorkingMemoryManager` siempre pasa 86400, pero `redis_set_json` acepta `None`; endurecer para que TTL sea obligatorio en datos conversacionales.

### 2.13. `docker-compose.yml` — ⚠️ 2 hallazgos

| ID | Severidad (local) | Hallazgo | Corrección |
|---|---|---|---|
| SEC-20 | Media (local) / Alta (si se expone) | PostgreSQL `nucleo/nucleo` y Redis **sin contraseña**, ambos publicados a todas las interfaces (`0.0.0.0:5433`, `0.0.0.0:6379`). En la laptop de desarrollo con firewall activo es tolerable; en cualquier red no confiable es toma de control de memoria y auditoría. | Para desarrollo: bind a `127.0.0.1:5433:5432` y `127.0.0.1:6379:6379`. Para producción: sin publicación de puertos, red interna + secrets en Docker/Compose. |
| SEC-21 | Media | El servicio `api` no tiene `healthcheck` ni límites de recursos, y hereda `.env` completo (todos los secretos visibles para cualquier proceso del contenedor; incluidos futuros `LLM_API_KEY`). | Añadir `healthcheck` y pasar solo variables necesarias; nunca logs de `.env`. |
| SEC-22 | Baja | El `api` en Compose no arranca porque `docker-compose.yml` usa imagen construida sin `PYTHONPATH` correcto — verificar (`PYTHONPATH=/app/src` o la forma `--app-dir src`). Además, el Dockerfile copia solo `src` pero ejecuta `cognitive_assistant.main:app` con `--app-dir src`, correcto; revisar `requirements.txt` incluya todas las deps actuales (pytest en imagen de producción es superficie extra). | Separar `requirements.txt` (runtime) de dev-deps; validar `docker compose up --build` en CI cada semana. |

### 2.14. `Dockerfile` — ⚠️ 1 hallazgo

| ID | Severidad | Hallazgo | Corrección |
|---|---|---|---|
| SEC-23 | Media | El contenedor corre como **root** (no hay `USER`), y el healthcheck usa `curl` instalado (ok), pero no hay multi-stage ni usuario sin privilegios. La Capa 7 (sandbox) exige imagen con usuario `non-root` precisamente para esto. | Añadir `RUN useradd -m appuser && USER appuser`, multi-stage si crece. |

### 2.15. `.env.example`, `.gitignore`, `main.py`, `__init__.py`s — ✅ sin hallazgos relevantes

- `.env` real **no** está versionado (`git ls-files` solo muestra `.env.example`) — control correcto.
- `.gitignore` excluye `.env`, `.venv`, `repos/`, volúmenes Docker — correcto.
- `main.py` ejecuta con `reload=True` — aceptable en dev; documentar que no va a producción.

### 2.16. Higiene del repo (riesgo operativo, no exploit)

- **Duplicación de informes** (`DATA/INFORME_AVANCE_DIA_*.md` vs `DATA/INFORMES/…`): dos fuentes de verdad divergirán → decisiones de seguridad basadas en claim desactualizado. Mantener solo `DATA/INFORMES/`.
- **7 archivos modificados + 6 rutas sin trackear** sin commit: el estado auditado no es reproducible por hash de commit. Commitear antes de continuar (instrucción ya dada).

---

## 3. Matriz Priorizada de Remediación

| Orden | ID | Acción | Esfuerzo | Bloquea |
|---|---|---|---|---|
| **P0-1** | SEC-06/09/10 | **Capa 3 completa** (fase 3 del plan Día 2): `PromptGuard`, sanitizer NFKC, interceptor 403 (RFC 7807), auditoría de violaciones, clasificador de sensibilidad antes de `consolidate`. | 1 día | Fase 4 (herramientas), cualquier LLM real. |
| **P0-2** | SEC-03/05/12 | **Autenticación mínima** (API key por ahora) y eliminación de `user_id`/`session_id` autodeclarados como identidad. CORS deliberado. | 0.5 día | Exposición fuera de localhost, memoria multiusuario real. |
| **P0-3** | SEC-19 | URL validator (esquema + DNS + rangos privados) antes de cablear `ToolRegistry`/ReAct. | 2 horas | Fase 4 del Día 2. |
| **P1-4** | SEC-02 | Rate limiter Token Bucket (Redis) en middleware; el plan lo exige desde el Día 05. | 0.5 día | Demo pública / Escenario 7 (ráfaga de 50). |
| **P1-5** | SEC-07 | `max_length=8000` en `content` + rechazo de caracteres de control. | 15 minutos | Todo payload grande. |
| **P1-6** | SEC-17 | Validación de `X-Trace-ID` entrante (UUIDv4 o regenerar). | 15 minutos | Integridad forense (Escenario 7). |
| **P1-7** | SEC-08/16 | Scrubber PII pre-auditoría + rol DB de solo INSERT. | 0.5 día | Cumplimiento y Escenario 7. |
| **P2-8** | SEC-01/20/23 | Bind a localhost en Compose dev, credenciales via env sin defaults, `USER` no-root, usuario DDL vs DML. | 0.5 día | Empaquetado Docker final (Día 40). |
| **P2-9** | SEC-14/15/18 | Errores genéricos al cliente, flag `mock` explícito, filtro de logs sin side-effects. | 1 hora | Hardening final. |

---

## 4. Divergencias Detectadas entre Declarado y Real

| Afirmación (informes/planes) | Realidad verificada en código | Impacto |
|---|---|---|
| "Rate limiting Token Bucket sobre Redis" (objetivo Semana 1, `.env` tiene `RATE_LIMIT_ENABLED=true`) | **No existe ninguna implementación** (`rate_limit` solo aparece en `settings.py`). | Config falsa-positiva: el sistema NO limita peticiones abusivas. |
| "PostgreSQL y audit persisten inmutablemente" | Funciona, pero mismo rol con DML total; sin alarmas ante fallback. | Auditoría suficiente para tesis, no inmutable de grado forense. |
| "Input sanitizado / contratos con longitudes" (plan Día 02 y Día 3.2) | `content` sin `max_length` en los 2 endpoints públicos. | DoS/coste no acotado. |
| "Timeout de navegación optimizado" (plan Día 2, Etapa 4.3) | Sigue en `timeout_ms=20000`. | Pendiente real; la suite completa colgada (>2 min) en la verificación de esta sesión es coherente con esto. |

## 5. Conclusión

El tronco encefálico es **estructuralmente bien construido** pero hoy es un organismo **sin sistema inmunológico ni piel**: memoria, deliberación y auditoría funcionan internamente mientras todo el perímetro está abierto. Esto está dentro de lo esperado para el Día 2 del plan — **la gravedad no es que existan estas brechas, sino el orden en que se cierren.**

**Regla de avance recomendada (derivada de esta auditoría):** no ejecutar la Fase 4 (herramientas autónomas/ReAct) hasta cerrar P0-1, P0-2 y P0-3. Conectar un navegador web + LLM + memoria persistente sin gobernanza convierte tres hallazgos latentes (prompt injection, memory poisoning, SSRF) en una sola cadena de ataque explotable de extremo a extremo.

---
*Auditoría generada por revisión estática exhaustiva de los 30 archivos Python, `docker-compose.yml`, `Dockerfile`, `.env.example`, `.gitignore` y contratos de la rama `semana1-tronco-encefalico`.*
