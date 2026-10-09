"""Validador y Cortafuegos de URLs Salientes (Política Anti-SSRF).

Previene ataques Server-Side Request Forgery (SSRF) verificando esquemas permitidos,
resolución DNS y denegando tráfico hacia direcciones de loopback, redes privadas (RFC 1918),
enlace local (link-local) y servicios de metadatos de proveedores cloud.
"""

import ipaddress
import socket
from urllib.parse import urlparse

from cognitive_assistant.shared.telemetry.logging import get_logger

logger = get_logger("cognitive_assistant.tools.url_validator")

ALLOWED_SCHEMES = {"http", "https"}
FORBIDDEN_HOSTS = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "metadata.google.internal",
    "instance-data",
}
CLOUD_METADATA_IPS = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("fd00:ec2::254"),
}


def validate_outbound_url(url: str) -> None:
    """
    Valida exhaustivamente una URL saliente antes de realizar cualquier petición o navegación.
    
    Lanza:
        ValueError: Si la URL infringe las políticas de seguridad anti-SSRF.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL saliente inválida o vacía.")

    parsed = urlparse(url)

    # 1. Validación de esquema
    if not parsed.scheme or parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError(
            f"Esquema no permitido '{parsed.scheme}'. Solo se autorizan esquemas http y https."
        )

    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"No se pudo extraer un hostname válido de la URL '{url}'.")

    hostname_lower = hostname.lower().strip()

    # 2. Validación de nombres de host prohibidos
    if hostname_lower in FORBIDDEN_HOSTS or hostname_lower.endswith(".internal"):
        raise ValueError(
            f"Destino no permitido: Host '{hostname}' pertenece a la red interna o local."
        )

    # 3. Resolución DNS e inspección de direcciones IP
    try:
        # Resolver direcciones IPv4 e IPv6
        addr_info = socket.getaddrinfo(hostname_lower, None)
    except socket.gaierror as exc:
        raise ValueError(f"Fallo en resolución DNS para el host '{hostname}': {exc}") from exc

    resolved_ips = set()
    for item in addr_info:
        sockaddr = item[4]
        ip_str = sockaddr[0]
        try:
            resolved_ips.add(ipaddress.ip_address(ip_str))
        except ValueError:
            continue

    if not resolved_ips:
        raise ValueError(f"No se obtuvieron direcciones IP válidas para el host '{hostname}'.")

    # 4. Inspección contra rangos no enrutables públicamente
    for ip in resolved_ips:
        if (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
            or ip in CLOUD_METADATA_IPS
        ):
            logger.warning(
                "Intento de SSRF bloqueado: URL='%s' resuelve a dirección restringida/privada (%s)",
                url,
                ip,
            )
            raise ValueError(
                f"Acceso denegado: El destino resuelve a la dirección IP privada o restringida ({ip}) por política anti-SSRF."
            )
