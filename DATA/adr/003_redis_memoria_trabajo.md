# ADR 003: Redis para Memoria de Trabajo Volátil y Control de Tasa

## Estado
Aceptado

## Contexto
La memoria de trabajo del ciclo cognitivo (Capa 4) requiere lecturas y escrituras ultrarrápidas (<20ms) de estados conversacionales activos, planes en progreso y ventana deslizante de turnos, además de requerir un mecanismo distribuido para rate limiting en Capa 2.

## Decisión
Implementar la **Memoria de Trabajo y Token Bucket Rate Limiting sobre Redis 7**:
- Almacenamiento en estructuras de clave-valor JSON y Hashes indexados por `session_id`.
- Políticas de expiración automática (TTL) para evitar saturación de memoria en sesiones inactivas.
- Scripts Lua o contadores atómicos para el algoritmo Token Bucket de Capa 2.

## Consecuencias
- **Positivas:** Latencia sub-milisegundo, expiración automática nativa, desacoplamiento del ciclo de persistencia lenta en disco.
- **Negativas:** La información no persistida en PostgreSQL se pierde si Redis se reinicia sin persistencia AOF/RDB adecuada.
