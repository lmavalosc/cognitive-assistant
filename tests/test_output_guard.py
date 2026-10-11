import pytest
from cognitive_assistant.modules.c3_governance.output_guard import OutputGuard, OutputFilterResult


def test_output_guard_clean_response():
    """Verifica que una respuesta limpia y legítima no sea alterada y leak_detected sea False."""
    text = "El ciclo cognitivo se completó con éxito. Aquí tienes el resumen del análisis."
    result = OutputGuard.filter_response(text, trace_id="trace-clean-123")

    assert isinstance(result, OutputFilterResult)
    assert result.sanitized_content == text
    assert result.leak_detected is False
    assert len(result.reasons) == 0
    assert result.trace_id == "trace-clean-123"


def test_output_guard_redacts_google_api_key():
    """Verifica que llaves de API de Google (AIzaSy...) sean ofuscadas."""
    text = "Tu clave de Gemini es AIzaSyD4g7H8j9K0L1M2N3P4Q5R6S7T8U9V0W1X para pruebas."
    result = OutputGuard.filter_response(text, trace_id="trace-google-key")

    assert result.leak_detected is True
    assert "AIzaSy" not in result.sanitized_content
    assert "[REDACTED_GOOGLE_API_KEY]" in result.sanitized_content
    assert any("AIzaSy" in r for r in result.reasons)


def test_output_guard_redacts_openai_and_generic_keys():
    """Verifica que llaves tipo sk-... o ghp-... sean neutralizadas."""
    text = "Usando sk-abcdef12345678901234567890123456 y ghp_123456789012345678901234567890."
    result = OutputGuard.filter_response(text)

    assert result.leak_detected is True
    assert "sk-abcdef" not in result.sanitized_content
    assert "ghp_12345" not in result.sanitized_content
    assert "[REDACTED_API_KEY]" in result.sanitized_content


def test_output_guard_redacts_database_uris():
    """Verifica que cadenas de conexión a base de datos con contraseñas sean ofuscadas."""
    text = "Conéctate usando postgresql://superadmin:P@ssw0rd123@prod-db.internal:5432/core_db para ver las tablas."
    result = OutputGuard.filter_response(text)

    assert result.leak_detected is True
    assert "P@ssw0rd123" not in result.sanitized_content
    assert "superadmin" not in result.sanitized_content
    assert "[REDACTED_USER]:[REDACTED_PASS]@[REDACTED_HOST]" in result.sanitized_content


def test_output_guard_redacts_passwords_and_tokens():
    """Verifica que contraseñas explícitas en texto plano sean interceptadas."""
    text1 = "El usuario fue creado con password: SuperSecretMasterKey!2026."
    result1 = OutputGuard.filter_response(text1)
    assert result1.leak_detected is True
    assert "SuperSecretMasterKey!2026" not in result1.sanitized_content
    assert "password=[REDACTED_SECRET]" in result1.sanitized_content

    text2 = "Credenciales generadas: contraseña = MiClavePrivada999."
    result2 = OutputGuard.filter_response(text2)
    assert result2.leak_detected is True
    assert "MiClavePrivada999" not in result2.sanitized_content


def test_output_guard_empty_response():
    """Verifica comportamiento seguro con cadenas vacías."""
    result = OutputGuard.filter_response("", trace_id="trace-empty")
    assert result.sanitized_content == ""
    assert result.leak_detected is False
    assert result.trace_id == "trace-empty"
