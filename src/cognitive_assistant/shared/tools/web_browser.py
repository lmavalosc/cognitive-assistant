"""Herramientas de Navegación y Extracción Web (Playwright + Firecrawl).

Permite al asistente cognitivo percibir contenido web, interactuar con páginas
y extraer markdown limpio para enriquecer el contexto deliberativo.
"""

import os
from typing import Any, Dict, Optional
from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id

logger = get_logger("cognitive_assistant.tools.web")


class PlaywrightBrowserTool:
    """Herramienta de navegación y scraping headless basada en Playwright."""

    def __init__(self, channel: str = "msedge", headless: bool = True) -> None:
        self.channel = channel
        self.headless = headless

    async def fetch_page_content(
        self,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout_ms: int = 20000,
    ) -> Dict[str, Any]:
        """
        Navega a una URL y extrae el título, texto plano y metadatos.
        """
        trace_id = get_trace_id()
        logger.info("Navegando a '%s' con Playwright (channel=%s, trace_id=%s)", url, self.channel, trace_id)

        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            try:
                # Intentar primero con el canal especificado (ej. msedge preinstalado en Windows)
                browser = await p.chromium.launch(
                    channel=self.channel,
                    headless=self.headless,
                )
            except Exception as launch_exc:
                logger.warning(
                    "Fallo al lanzar navegador con canal '%s' (%s). Intentando chromium por defecto.",
                    self.channel,
                    launch_exc,
                )
                browser = await p.chromium.launch(headless=self.headless)

            try:
                context = await browser.new_context(
                    user_agent="CognitiveAssistant/0.1.0 (Web Perception Engine)"
                )
                page = await context.new_page()
                page.set_default_timeout(timeout_ms)

                await page.goto(url, wait_until=wait_until)
                title = await page.title()
                content = await page.inner_text("body")

                logger.info("Página obtenida exitosamente: '%s' (%d caracteres)", title, len(content))
                return {
                    "url": url,
                    "title": title,
                    "content": content[:5000],  # Truncamiento defensivo
                    "trace_id": trace_id,
                    "status": "success",
                }
            except Exception as exc:
                logger.error("Error al navegar a '%s': %s", url, exc)
                return {
                    "url": url,
                    "title": "",
                    "content": "",
                    "error": str(exc),
                    "trace_id": trace_id,
                    "status": "error",
                }
            finally:
                await browser.close()


class FirecrawlTool:
    """Herramienta de extracción profunda en formato Markdown mediante Firecrawl."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.api_url = api_url or os.getenv("FIRECRAWL_API_URL")
        self._app = None

        if self.api_key:
            from firecrawl import FirecrawlApp
            kwargs: Dict[str, Any] = {"api_key": self.api_key}
            if self.api_url:
                kwargs["api_url"] = self.api_url
            self._app = FirecrawlApp(**kwargs)

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Extrae el contenido de una URL en formato Markdown limpio.
        Si no hay API key configurada, delega a Playwright para extracción local.
        """
        trace_id = get_trace_id()
        logger.info("Extrayendo contenido de '%s' con Firecrawl (trace_id=%s)", url, trace_id)

        if self._app is not None:
            try:
                result = self._app.scrape_url(url, params={"formats": ["markdown", "html"]})
                markdown_text = result.get("markdown", "")
                return {
                    "url": url,
                    "markdown": markdown_text,
                    "trace_id": trace_id,
                    "provider": "firecrawl-cloud",
                    "status": "success",
                }
            except Exception as exc:
                logger.warning("Fallo en llamada a Firecrawl API: %s. Aplicando fallback local.", exc)

        # Fallback local usando PlaywrightBrowserTool
        browser_tool = get_playwright_tool()
        page_res = await browser_tool.fetch_page_content(url)
        return {
            "url": url,
            "markdown": f"# {page_res.get('title', '')}\n\n{page_res.get('content', '')}",
            "trace_id": trace_id,
            "provider": "playwright-local-fallback",
            "status": page_res.get("status", "success"),
        }


_browser_tool_instance: Optional[PlaywrightBrowserTool] = None


def get_playwright_tool() -> PlaywrightBrowserTool:
    """Retorna la instancia singleton de PlaywrightBrowserTool."""
    global _browser_tool_instance
    if _browser_tool_instance is None:
        _browser_tool_instance = PlaywrightBrowserTool()
    return _browser_tool_instance
