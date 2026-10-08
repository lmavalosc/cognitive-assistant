# Asistente Cognitivo — Etapa 1: Núcleo Transaccional (Tronco Encefálico)

Implementación mínima ejecutable y robusta del **Tronco Encefálico** (Núcleo Transaccional) para la tesis de Asistente Cognitivo, siguiendo el principio arquitectónico **Core-to-Periphery**.

---

## 🎯 Objetivos de la Etapa 1

- [x] **FastAPI arranca** de forma limpia y modular.
- [x] **`GET /health` responde 200 OK** con metadatos de estado operativo.
- [x] **Generación de `trace_id`** en cada solicitud entrante mediante middleware asíncrono y ContextVar.
- [x] **Devolución de `trace_id` en headers HTTP** (`X-Trace-ID`).
- [x] **Inyección de `trace_id` en logs estructurados** automáticamente (`TraceIdFilter`).
- [x] **Docker Compose** orquestando API + PostgreSQL 16 + Redis 7 con healthchecks.
- [x] **Módulos semilla**:
  - `c2_reception`: Recepción transaccional y validación de entrada.
  - `c8_effectors`: Despachador de eventos y salida con trazabilidad.

---

## 📂 Estructura del Proyecto

```text
cognitive-assistant/
├── README.md
├── pyproject.toml
├── .env.example
├── .env
├── .gitignore
├── docker-compose.yml
├── Dockerfile
│
├── src/
│   └── cognitive_assistant/
│       ├── __init__.py
│       ├── main.py
│       ├── app.py
│       ├── settings.py
│       │
│       ├── shared/
│       │   ├── __init__.py
│       │   └── telemetry/
│       │       ├── __init__.py
│       │       ├── logging.py
│       │       └── trace.py
│       │
│       └── modules/
│           ├── __init__.py
│           ├── c2_reception/
│           │   ├── __init__.py
│           │   ├── router.py
│           │   └── schemas.py
│           └── c8_effectors/
│               ├── __init__.py
│               └── dispatcher.py
│
└── tests/
    ├── __init__.py
    ├── test_health.py
    └── test_trace.py
```

---

## 🚀 Puesta en Marcha Local

### 1. Requisitos Previos

- Python 3.11+ (o 3.12)
- [uv](https://github.com/astral-sh/uv) (recomendado) o `pip` / `venv`
- Docker y Docker Compose

### 2. Configurar Entorno Virtual e Instalar Dependencias

Con **uv**:
```powershell
uv venv .venv
.\.venv\Scripts\Activate.ps1
uv pip install -e ".[dev]"
```

Con **pip** estándar:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 3. Ejecutar el Servidor en Modo Desarrollo

```powershell
uvicorn cognitive_assistant.main:app --reload --host 0.0.0.0 --port 8000
```

O directamente ejecutando el módulo:
```powershell
python src/cognitive_assistant/main.py
```

### 4. Verificar Endpoints

- **Health check:**
  ```bash
  curl -i http://localhost:8000/health
  ```
  *Respuesta esperada:*
  ```http
  HTTP/1.1 200 OK
  x-trace-id: 3c9b4e6d2a1f4b8c9d0e1f2a3b4c5d6e
  content-type: application/json

  {"status":"ok","app":"Cognitive Assistant","version":"0.1.0","trace_id":"3c9b4e6d2a1f4b8c9d0e1f2a3b4c5d6e"}
  ```

- **Documentación Swagger UI interactiva:**
  Visita [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Ejecución de Pruebas

Para ejecutar la suite de pruebas unitarias y de integración de trazabilidad:

```powershell
pytest -v
```

---

## 🐳 Despliegue con Docker Compose

Para levantar el entorno completo (API + PostgreSQL 16 + Redis 7):

```powershell
docker compose up --build -d
```

Verificar estado de los contenedores:
```powershell
docker compose ps
```

Ver los logs en tiempo real:
```powershell
docker compose logs -f api
```

Detener los servicios:
```powershell
docker compose down
```

---

## 🛡️ Principios del Tronco Encefálico

1. **Sin Estado Oculto:** Toda petición tiene un `trace_id` inyectado en el contexto de ejecución.
2. **Alta Resiliencia:** Servicios periféricos (PostgreSQL, Redis) cuentan con sondas de `healthcheck`.
3. **Desacoplamiento Modular:** La recepción (`c2_reception`) está separada de los efectores (`c8_effectors`) a través del despachador de eventos.
