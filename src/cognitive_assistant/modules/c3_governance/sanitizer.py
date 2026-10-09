"""Sanitizador defensivo de entradas perimétricas para Capa 3."""
import re
import unicodedata
from typing import Tuple

# Caracteres de control ASCII no permitidos (excluyendo \t, \n, \r)
_CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MAX_CONTENT_LENGTH = 8000


class InputSanitizer:
    """Higieniza y normaliza estímulos de texto antes del análisis heurístico."""

    @staticmethod
    def sanitize(content: str) -> Tuple[str, bool, bool]:
        """
        Sanitiza el contenido.
        Retorna (contenido_limpio, tenia_caracteres_invalidos, supera_limite_longitud).
        """
        had_invalid_chars = False
        was_oversized = False

        if not content:
            return "", False, False

        # 1. Normalización Unicode NFKC para neutralizar ataques de homóglifos y bypass de codificación
        normalized = unicodedata.normalize("NFKC", content)

        # 2. Detección y remoción de caracteres nulos y de control no imprimibles
        if _CONTROL_CHAR_REGEX.search(normalized):
            had_invalid_chars = True
            normalized = _CONTROL_CHAR_REGEX.sub("", normalized)

        # 3. Límite de longitud estricto
        if len(normalized) > MAX_CONTENT_LENGTH:
            was_oversized = True
            normalized = normalized[:MAX_CONTENT_LENGTH]

        # 4. Limpieza de bordes
        sanitized = normalized.strip()

        return sanitized, had_invalid_chars, was_oversized
