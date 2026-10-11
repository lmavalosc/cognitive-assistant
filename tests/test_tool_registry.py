"""Pruebas unitarias para el Registro de Herramientas Periféricas (ToolRegistry) y Calculadora AST.

Valida contratos Pydantic v2, introspección, ejecución controlada y límites de seguridad matemática.
"""

import math
import pytest
from cognitive_assistant.shared.tools.registry import (
    ToolDefinition,
    ToolParameter,
    ToolRequest,
    ToolResult,
    ToolRiskLevel,
    get_tool_registry,
    safe_calculator_handler,
)


@pytest.fixture
def registry():
    return get_tool_registry()


def test_tool_registry_introspection(registry):
    """Verifica que el catálogo registre las herramientas nativas con contratos y riesgos válidos."""
    tools = registry.list_tools()
    assert len(tools) >= 3

    tool_names = {t.name for t in tools}
    assert "calculator_safe" in tool_names
    assert "web_search_and_read" in tool_names
    assert "system_command_mock" in tool_names

    calc_def = registry.get_tool("calculator_safe")
    assert calc_def is not None
    assert calc_def.risk_level == ToolRiskLevel.LOW
    assert calc_def.requires_approval is False
    assert "expression" in calc_def.parameters
    assert calc_def.parameters["expression"].required is True

    cmd_def = registry.get_tool("system_command_mock")
    assert cmd_def is not None
    assert cmd_def.risk_level == ToolRiskLevel.CRITICAL
    assert cmd_def.requires_approval is True


@pytest.mark.asyncio
async def test_calculator_basic_arithmetic():
    """Verifica operaciones aritméticas elementales con precisión decimal."""
    res = await safe_calculator_handler("15 * 4 + 10 / 2 - 3")
    assert res["result"] == 62.0

    res_neg = await safe_calculator_handler("-5 * (-2) + (+3)")
    assert res_neg["result"] == 13.0

    res_mod = await safe_calculator_handler("17 % 5")
    assert res_mod["result"] == 2.0


@pytest.mark.asyncio
async def test_calculator_math_functions():
    """Verifica invocación segura de funciones matemáticas permitidas (sqrt, abs, round, min, max)."""
    res_sqrt = await safe_calculator_handler("sqrt(144) + abs(-10)")
    assert res_sqrt["result"] == 22.0

    res_funcs = await safe_calculator_handler("min(10, 20) + max(5, round(3.7))")
    assert res_funcs["result"] == 15.0


@pytest.mark.asyncio
async def test_calculator_power_both_syntaxes():
    """Verifica que la calculadora soporte potencia tanto con ** (Python) como con ^ (notación matemática estándar)."""
    # 2 ** 3
    res_pow_py = await safe_calculator_handler("2 ** 3")
    assert res_pow_py["result"] == 8.0

    # 2 ^ 3 (notación matemática descrita en el documento de especificación de Fase 4)
    res_pow_caret = await safe_calculator_handler("2 ^ 3")
    assert res_pow_caret["result"] == 8.0

    # Expresión canónica exacta de FASE_4_ESPECIFICACION_Y_REQUISITOS.md: (15 * 4) + sqrt(144) - 2^3
    res_spec = await safe_calculator_handler("(15 * 4) + sqrt(144) - 2^3")
    # (15 * 4) = 60; sqrt(144) = 12; 2^3 = 8 -> 60 + 12 - 8 = 64
    assert res_spec["result"] == 64.0


@pytest.mark.asyncio
async def test_calculator_division_by_zero_fails():
    """Verifica que la división por cero arroje ZeroDivisionError controlado."""
    with pytest.raises(ZeroDivisionError, match="División por cero"):
        await safe_calculator_handler("10 / 0")

    with pytest.raises(ZeroDivisionError, match="División por cero"):
        await safe_calculator_handler("10 // 0")

    with pytest.raises(ZeroDivisionError, match="División por cero"):
        await safe_calculator_handler("10 % 0")


@pytest.mark.asyncio
async def test_calculator_magnitude_and_length_limits():
    """Verifica restricciones de longitud de expresión y límites exponenciales contra ataques DoS."""
    # Exceso de longitud > 200 caracteres
    long_expr = "1 + " * 100 + "1"
    with pytest.raises(ValueError, match="excede el límite de 200 caracteres"):
        await safe_calculator_handler(long_expr)

    # Exponente excesivo
    with pytest.raises(ValueError, match="límites de seguridad"):
        await safe_calculator_handler("2 ** 1001")


@pytest.mark.asyncio
async def test_calculator_blocks_malicious_code_injection():
    """Verifica que llamadas a builtins peligrosos, accesos a atributos o imports sean rechazados."""
    hostile_expressions = [
        "__import__('os').system('ls')",
        "open('/etc/passwd').read()",
        "eval('2 + 2')",
        "exec('import sys')",
        "globals()",
        "locals()",
        "'a' + 'b'",
    ]
    for expr in hostile_expressions:
        with pytest.raises((ValueError, TypeError)):
            await safe_calculator_handler(expr)


@pytest.mark.asyncio
async def test_tool_registry_execute_tool(registry):
    """Verifica el despacho exitoso mediante ToolRegistry.execute_tool()."""
    req = ToolRequest(
        tool_name="calculator_safe",
        arguments={"expression": "100 / 4 + 5"},
        trace_id="test-trace-123",
        user_id="test_user",
    )
    result = await registry.execute_tool(req)
    assert isinstance(result, ToolResult)
    assert result.status == "success"
    assert result.tool_name == "calculator_safe"
    assert result.output["result"] == 30.0
    assert result.error is None
    assert result.trace_id == "test-trace-123"


@pytest.mark.asyncio
async def test_tool_registry_execute_unregistered_tool(registry):
    """Verifica que ejecutar una herramienta no registrada devuelva un ToolResult de error controlado."""
    req = ToolRequest(
        tool_name="unknown_external_tool",
        arguments={},
        trace_id="test-trace-404",
    )
    result = await registry.execute_tool(req)
    assert result.status == "error"
    assert "no está registrada" in result.error.lower() or "no encontrada" in result.error.lower()
