import pytest
import psycopg2
from pgvector.psycopg2 import register_vector
from cognitive_assistant.settings import settings


def test_postgres_pgvector_live_connection():
    """Verifica conexión real a PostgreSQL y soporte de pgvector en el contenedor Docker."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            connect_timeout=3,
        )
    except Exception as exc:
        pytest.skip(f"Contenedor PostgreSQL no accesible localmente: {exc}")

    try:
        cur = conn.cursor()
        register_vector(conn)

        cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        row = cur.fetchone()
        assert row is not None
        assert row[0] == "vector"

        # Prueba de inserción y cálculo de distancia
        cur.execute("CREATE TEMPORARY TABLE items (id serial PRIMARY KEY, embedding vector(3));")
        cur.execute("INSERT INTO items (embedding) VALUES ('[1,0,0]'), ('[0,1,0]');")
        cur.execute("SELECT id, embedding <-> '[1,0,0]' FROM items ORDER BY embedding <-> '[1,0,0]';")
        results = cur.fetchall()
        assert len(results) == 2
        assert results[0][1] == 0.0

        cur.close()
    finally:
        conn.close()
