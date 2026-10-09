"""Motor de detección heurística de ataques y manipulación semántica (PromptGuard).

Analiza patrones adversarios de Prompt Injection, Jailbreak y fuga de instrucciones
de sistema con tiempos de respuesta deterministas menores a 2 milisegundos.
"""
import re
from typing import List, Tuple
from cognitive_assistant.modules.c3_governance.schemas import ViolationType

# 1. Patrones de Anulación e Inyección de Prompts
_INJECTION_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|commands|guidelines)\b",
    r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)\b",
    r"(?i)\bforget\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)\b",
    r"(?i)\b(system\s+override|override\s+system\s+prompt|bypass\s+(safety|guardrails|system|filters))\b",
    r"(?i)\b(ignora|olvida|descarta)\s+(todas\s+)?las\s+instrucciones\s+(previas|anteriores)\b",
    r"(?i)\b(anula|omite)\s+las\s+reglas\s+(previas|anteriores|del\s+sistema)\b",
    r"(?i)\bnew\s+instructions?\s*:\s*(you\s+are\s+now|act\s+as)\b",
]

# 2. Patrones de Intento de Jailbreak (Modo DAN, Personas sin restricciones)
_JAILBREAK_PATTERNS = [
    r"(?i)\b(dan\s+mode|do\s+anything\s+now)\b",
    r"(?i)\bdeveloper\s+mode\s+(enabled|on|activate|activated)\b",
    r"(?i)\bmodo\s+desarrollador\s+(activado|habilitado|encendido)\b",
    r"(?i)\bpretend\s+(you\s+have\s+no\s+limits|you\s+are\s+unfiltered|you\s+are\s+evil|you\s+have\s+no\s+rules)\b",
    r"(?i)\b(act\s+as|pretend\s+to\s+be)\s+an?\s+(unrestricted|unfiltered|jailbroken)\s+(ai|assistant|model)\b",
    r"(?i)\bact[úu]a\s+como\s+una?\s+(ia|asistente)\s+(sin\s+restricciones|sin\s+l[íi]mites|desfiltrada)\b",
    r"(?i)\bjailbreak(\s+prompt|\s+mode)?\b",
    r"(?i)\byou\s+are\s+now\s+free\s+from\s+all\s+(rules|guidelines|restrictions)\b",
]

# 3. Patrones de Fuga o Exfiltración de Contexto y Secretos
_LEAK_PATTERNS = [
    r"(?i)\b(print|show|reveal|display|output|dump|repeat|tell\s+me)\s+(your\s+)?(system\s+prompt|system\s+instructions|initial\s+prompt|hidden\s+prompt)\b",
    r"(?i)\b(muestra|imprime|revela|dime|repite)\s+(tu\s+)?(prompt\s+de\s+sistema|instrucciones\s+del\s+sistema|prompt\s+inicial)\b",
    r"(?i)\b(dump|show|print)\s+(all\s+)?(api\s+keys?|environment\s+variables?|env\s+vars?|secrets?|passwords?)\b",
    r"(?i)\b(muestra|imprime)\s+(las\s+)?(claves\s+api|variables\s+de\s+entorno|secretos|contrase[ñn]as)\b",
]

_COMPILED_INJECTIONS = [re.compile(p) for p in _INJECTION_PATTERNS]
_COMPILED_JAILBREAKS = [re.compile(p) for p in _JAILBREAK_PATTERNS]
_COMPILED_LEAKS = [re.compile(p) for p in _LEAK_PATTERNS]


class PromptGuard:
    """Clasificador heurístico determinista perimétrico."""

    @classmethod
    def evaluate(cls, content: str) -> Tuple[float, ViolationType, List[str]]:
        """
        Evalúa el texto y determina el score de riesgo, tipo de violación y coincidencias encontradas.
        Retorna (risk_score, violation_type, matched_signatures).
        """
        if not content:
            return 0.0, ViolationType.NONE, []

        matches: List[str] = []

        # 1. Comprobar Jailbreak (Máxima prioridad de amenaza)
        for pattern in _COMPILED_JAILBREAKS:
            found = pattern.findall(content)
            if found:
                matches.append(pattern.pattern)
        if matches:
            return 0.95, ViolationType.JAILBREAK_ATTEMPT, matches

        # 2. Comprobar Inyección de Prompts
        for pattern in _COMPILED_INJECTIONS:
            found = pattern.findall(content)
            if found:
                matches.append(pattern.pattern)
        if matches:
            return 0.85, ViolationType.PROMPT_INJECTION, matches

        # 3. Comprobar Fuga de Prompts del Sistema
        for pattern in _COMPILED_LEAKS:
            found = pattern.findall(content)
            if found:
                matches.append(pattern.pattern)
        if matches:
            return 0.75, ViolationType.SYSTEM_PROMPT_LEAK, matches

        # Estímulo benigno
        return 0.0, ViolationType.NONE, []
