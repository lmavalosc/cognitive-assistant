import pytest
import asyncpg
from cognitive_assistant.settings import settings


@pytest.mark.asyncio
async def test_postgres_pgvector_live_connection():
    """Verifica conexión real a PostgreSQL y soporte de pgvector mediante asyncpg en el puerto activo."""
    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        timeout=5,
    )
    try:
        # Verificar extensión vector
        ext = await conn.fetchval("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        assert ext == "vector"

        # Prueba de inserción y cálculo de distancia vectorial
        await conn.execute("CREATE TEMPORARY TABLE items (id serial PRIMARY KEY, embedding vector(3));")
        await conn.execute("INSERT INTO items (embedding) VALUES ('[1,0,0]'), ('[0,1,0]');")
        results = await conn.fetch("SELECT id, embedding <-> '[1,0,0]' AS dist FROM items ORDER BY dist;")
        assert len(results) == 2
        assert float(results[0]["dist"]) == 0.0
        assert float(results[1]["dist"]) > 0.0
    finally:
        await conn.close()

