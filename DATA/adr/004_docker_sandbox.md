# ADR 004: Aislamiento Operacional de Herramientas mediante Docker SDK

## Estado
Aceptado

## Contexto
Los agentes de la Capa 6 (ej. Agente Programador) pueden generar código arbitrario o requerir ejecución de comandos para resolver tareas complejas. Ejecutar código generado directamente en el servidor anfitrión introduce riesgos inaceptables de escalada de privilegios y ataques a la infraestructura.

## Decisión
Confinar la ejecución de herramientas (Capa 7) mediante contenedores efímeros creados mediante **Docker SDK**:
- Aislamiento total de red: `network_mode="none"`.
- Límites estrictos de memoria RAM: `mem_limit="256m"`.
- Límites de CPU: `nano_cpus=1000000000` (1 core).
- Timeout forzoso de 15.0 segundos con destrucción automática del contenedor.
- Sistema de archivos efímero de sólo lectura excepto por un directorio temporal `/tmp`.

## Consecuencias
- **Positivas:** Seguridad robusta contra ataques de ejecución de código arbitrario, mitigación de bucles infinitos y exfiltración de datos.
- **Negativas:** Sobrecarga de tiempo en el inicio de contenedores si no se reutilizan imágenes precalentadas o pools de contenedores.
