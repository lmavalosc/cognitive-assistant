"""Registro Tipado de Herramientas Periféricas (ToolRegistry).

Define contratos Pydantic estrictos para introspección, validación de parámetros,
clasificación de riesgo y despacho seguro de herramientas cognitivas (Capa 8 / C8 Sandbox).
"""

import ast
import math
import operator
import re
import time
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id
from cognitive_assistant.shared.tools.url_validator import validate_outbound_url
from cognitive_assistant.shared.tools.web_browser import FirecrawlTool

logger = get_logger("cognitive_assistant.tools.registry")


class ToolRiskLevel(str, Enum):
    """Clasificación de riesgo de herramientas según la Capa 3 (Gobernanza de Acción)."""
    LOW = "LOW"            # Lectura pura, cálculos deterministas sin acceso a red sensible
    MED = "MED"            # Acceso a red saliente controlada (anti-SSRF verificado)
    HIGH = "HIGH"          # Modificación de estado interno o llamadas a APIs autenticadas
    CRITICAL = "CRITICAL"  # Operaciones de sistema, destructivas o financieras (requiere HITL)


class ToolParameter(BaseModel):
    """Definición tipada de un parámetro de herramienta."""
    name: str = Field(..., description="Nombre del parámetro")
    type: str = Field(..., description="Tipo de dato primitivo ('string', 'int', 'float', 'bool')")
    description: str = Field(..., description="Descripción funcional del parámetro")
    required: bool = Field(default=True, description="Indica si el parámetro es obligatorio")
    default: Optional[Any] = Field(default=None, description="Valor por defecto si no es requerido")


class ToolDefinition(BaseModel):
    """Metadatos declarativos de una herramienta registrada."""
    name: str = Field(..., description="Identificador único de la herramienta")
    description: str = Field(..., description="Descripción detallada de la capacidad y uso")
    risk_level: ToolRiskLevel = Field(..., description="Nivel de riesgo para la gobernanza")
    parameters: Dict[str, ToolParameter] = Field(default_factory=dict, description="Diccionario de parámetros")
    requires_approval: bool = Field(default=False, description="Requiere confirmación HITL previa a la ejecución")


class ToolRequest(BaseModel):
    """Petición de ejecución de una herramienta formulada por el Ejecutivo Cognitivo."""
    tool_name: str = Field(..., description="Nombre de la herramienta solicitada")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Argumentos suministrados")
    trace_id: str = Field(default="", description="Identificador de trazabilidad distribuida")
    user_id: str = Field(default="default_user", description="Identificador del usuario")
    session_id: str = Field(default="default_session", description="Identificador de la sesión")
    hitl_approved: bool = Field(default=False, description="Bandera de autorización explícita Human-in-the-Loop")


class ToolResult(BaseModel):
    """Resultado estructurado de la ejecución de una herramienta."""
    tool_name: str = Field(..., description="Herramienta ejecutada")
    status: str = Field(..., description="Estado final ('success', 'error', 'blocked')")
    output: Optional[Any] = Field(default=None, description="Carga útil producida por la herramienta")
    error: Optional[str] = Field(default=None, description="Detalle del error o motivo de bloqueo si falló")
    duration_ms: float = Field(default=0.0, description="Tiempo de ejecución en milisegundos")
    risk_level: ToolRiskLevel = Field(default=ToolRiskLevel.LOW, description="Riesgo clasificado")
    trace_id: str = Field(default="", description="Trace ID asociado a la ejecución")


# ==========================================
# Implementación Segura: Calculadora AST
# ==========================================

_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.BitXor: operator.pow,  # Soporte de potencia en notación matemática estándar
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "pow": math.pow,
    "ceil": math.ceil,
    "floor": math.floor,
}


def _eval_ast_node(node: ast.AST) -> float:
    """Evalúa recursivamente un nodo de árbol de sintaxis abstracta de forma segura."""
    if isinstance(node, ast.Expression):
        return _eval_ast_node(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Tipo de constante no numérico: {type(node.value).__name__}")
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _SAFE_OPERATORS:
            operand_val = _eval_ast_node(node.operand)
            return _SAFE_OPERATORS[op_type](operand_val)
        raise ValueError(f"Operador unario no permitido: {op_type.__name__}")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in _SAFE_OPERATORS:
            left_val = _eval_ast_node(node.left)
            right_val = _eval_ast_node(node.right)
            if op_type in (ast.Pow, ast.BitXor) and (abs(right_val) > 100 or abs(left_val) > 10000):
                raise ValueError("Exponente o base excede los límites de seguridad numérica.")
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right_val == 0:
                raise ZeroDivisionError("División por cero no permitida.")
            return _SAFE_OPERATORS[op_type](left_val, right_val)
        raise ValueError(f"Operador binario no permitido: {op_type.__name__}")
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCTIONS:
            evaluated_args = [_eval_ast_node(arg) for arg in node.args]
            func = _SAFE_FUNCTIONS[node.func.id]
            return float(func(*evaluated_args))
        raise ValueError("Llamada a función no permitida en calculadora segura.")
    raise ValueError(f"Expresión no permitida: {type(node).__name__}")


async def safe_calculator_handler(expression: str) -> Dict[str, Any]:
    """Evalúa de forma segura una expresión matemática estricta sin acceso al sistema."""
    clean_expr = expression.strip()
    if len(clean_expr) > 200:
        raise ValueError("La expresión matemática excede el límite de 200 caracteres.")

    # Normalizar notación matemática estándar: convertir '^' en '**' para preservar precedencia
    normalized_expr = re.sub(r"\^", "**", clean_expr)

    parsed = ast.parse(normalized_expr, mode="eval")
    result = _eval_ast_node(parsed)
    return {
        "expression": clean_expr,
        "result": result,
    }


# ==========================================
# Implementación Segura: Web Search & Read
# ==========================================

async def web_search_and_read_handler(url: str) -> Dict[str, Any]:
    """Navega y extrae contenido web en Markdown previa validación anti-SSRF."""
    # Validación anti-SSRF estricta
    validate_outbound_url(url)
    
    tool = FirecrawlTool()
    res = await tool.scrape_url(url)
    return {
        "url": url,
        "markdown": res.get("markdown", "")[:4000],
        "provider": res.get("provider", "unknown"),
        "status": res.get("status", "success"),
    }


# ==========================================
# Mock Crítico: System Command (para HITL)
# ==========================================

async def system_command_mock_handler(command: str) -> Dict[str, Any]:
    """Herramienta simulada de alto riesgo para validar la gobernanza HITL."""
    return {
        "command": command,
        "executed": True,
        "output": f"Comando '{command}' ejecutado bajo autorización HITL.",
    }


# ==========================================
# Registro Central de Herramientas
# ==========================================

class ToolRegistry:
    """Catálogo centralizado de herramientas tipadas con introspección y despacho seguro."""

    def __init__(self) -> None:
        self._definitions: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable[..., Awaitable[Any]]] = {}

    def register_tool(
        self,
        definition: ToolDefinition,
        handler: Callable[..., Awaitable[Any]],
    ) -> None:
        """Registra una herramienta con sus metadatos y función asíncrona de ejecución."""
        self._definitions[definition.name] = definition
        self._handlers[definition.name] = handler
        logger.info(
            "Herramienta registrada en ToolRegistry: name='%s', risk='%s', params=%s",
            definition.name,
            definition.risk_level.value,
            list(definition.parameters.keys()),
        )

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Obtiene la definición de una herramienta por su nombre."""
        return self._definitions.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        """Retorna la lista completa de herramientas registradas."""
        return list(self._definitions.values())

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Retorna el esquema OpenAPI/JSON Schema de todas las herramientas registradas."""
        schemas = []
        for defn in self._definitions.values():
            schemas.append({
                "name": defn.name,
                "description": defn.description,
                "risk_level": defn.risk_level.value,
                "requires_approval": defn.requires_approval,
                "parameters": {
                    p_name: {
                        "type": p.type,
                        "description": p.description,
                        "required": p.required,
                        "default": p.default,
                    }
                    for p_name, p in defn.parameters.items()
                },
            })
        return schemas

    async def execute_tool(self, request: ToolRequest) -> ToolResult:
        """
        Ejecuta la herramienta solicitada despachando a su manejador registrado.
        Calcula latencia y atrapa excepciones garantizando estructura uniforme.
        """
        start_time = time.perf_counter()
        tool_name = request.tool_name
        trace_id = request.trace_id or get_trace_id()

        defn = self.get_tool(tool_name)
        if defn is None:
            return ToolResult(
                tool_name=tool_name,
                status="error",
                error=f"Herramienta '{tool_name}' no está registrada en el catálogo.",
                duration_ms=round((time.perf_counter() - start_time) * 1000, 2),
                risk_level=ToolRiskLevel.LOW,
                trace_id=trace_id,
            )

        handler = self._handlers.get(tool_name)
        if handler is None:
            return ToolResult(
                tool_name=tool_name,
                status="error",
                error=f"Manejador no configurado para la herramienta '{tool_name}'.",
                duration_ms=round((time.perf_counter() - start_time) * 1000, 2),
                risk_level=defn.risk_level,
                trace_id=trace_id,
            )

        try:
            logger.info(
                "Ejecutando herramienta '%s' (risk=%s, trace_id=%s)",
                tool_name,
                defn.risk_level.value,
                trace_id,
            )
            raw_output = await handler(**request.arguments)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            return ToolResult(
                tool_name=tool_name,
                status="success",
                output=raw_output,
                duration_ms=round(duration_ms, 2),
                risk_level=defn.risk_level,
                trace_id=trace_id,
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                "Error en ejecución de herramienta '%s' (trace_id=%s): %s",
                tool_name,
                trace_id,
                exc,
            )
            return ToolResult(
                tool_name=tool_name,
                status="error",
                error=str(exc),
                duration_ms=round(duration_ms, 2),
                risk_level=defn.risk_level,
                trace_id=trace_id,
            )


# ==========================================
# Instancia Singleton y Registro por Defecto
# ==========================================

_registry_instance: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Retorna la instancia global del ToolRegistry configurada con herramientas base."""
    global _registry_instance
    if _registry_instance is None:
        reg = ToolRegistry()

        # 1. Calculadora Segura (Cómputo determinista)
        reg.register_tool(
            definition=ToolDefinition(
                name="calculator_safe",
                description="Evalúa operaciones aritméticas deterministas (sumas, multiplicaciones, potencias, etc.) de manera segura.",
                risk_level=ToolRiskLevel.LOW,
                parameters={
                    "expression": ToolParameter(
                        name="expression",
                        type="string",
                        description="Expresión matemática a evaluar (ej: '25 * 40 + 12')",
                        required=True,
                    )
                },
                requires_approval=False,
            ),
            handler=safe_calculator_handler,
        )

        # 2. Navegador y Extractor Web (Percepción Externa)
        reg.register_tool(
            definition=ToolDefinition(
                name="web_search_and_read",
                description="Extrae y lee el contenido estructurado en Markdown de una página web pública previa validación de seguridad.",
                risk_level=ToolRiskLevel.MED,
                parameters={
                    "url": ToolParameter(
                        name="url",
                        type="string",
                        description="URL pública HTTP/HTTPS a inspeccionar",
                        required=True,
                    )
                },
                requires_approval=False,
            ),
            handler=web_search_and_read_handler,
        )

        # 3. Herramienta Crítica de Sistema (Para verificación HITL)
        reg.register_tool(
            definition=ToolDefinition(
                name="system_command_mock",
                description="Comando de sistema con impacto operacional elevado. Requiere autorización humana explícita.",
                risk_level=ToolRiskLevel.CRITICAL,
                parameters={
                    "command": ToolParameter(
                        name="command",
                        type="string",
                        description="Comando a simular",
                        required=True,
                    )
                },
                requires_approval=True,
            ),
            handler=system_command_mock_handler,
        )

        _registry_instance = reg

    return _registry_instance
