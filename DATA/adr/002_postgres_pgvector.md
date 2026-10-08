# ADR 002: Almacenamiento Dual en PostgreSQL con pgvector

## Estado
Aceptado

## Contexto
El sistema requiere almacenar simultáneamente registros estructurados relacionales (trazas de auditoría, sesiones, episodios, perfiles) y representaciones vectoriales densas de conocimiento (embeddings para RAG y memoria semántica).

## Decisión
Utilizar **PostgreSQL 16** con la extensión **pgvector**:
- Elimina la necesidad de operar una base de datos vectorial externa dedicada (como Milvus o Pinecone).
- Proporciona transaccionalidad ACID entre metadatos y vectores.
- Permite indexación HNSW (`vector_cosine_ops`) para búsqueda por similitud de alto rendimiento.

## Consecuencias
- **Positivas:** Simplicidad operativa, un único motor de base de datos relacional y vectorial, respaldos unificados.
- **Negativas:** Consumo de memoria RAM proporcional a los índices HNSW en colecciones muy masivas.
