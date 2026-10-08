"""Herramientas compartidas del asistente cognitivo (Navegación, Web y Scrapers)."""
from cognitive_assistant.shared.tools.web_browser import (
    FirecrawlTool,
    PlaywrightBrowserTool,
    get_playwright_tool,
)

__all__ = ["FirecrawlTool", "PlaywrightBrowserTool", "get_playwright_tool"]
