import pytest
from cognitive_assistant.shared.tools.web_browser import FirecrawlTool, PlaywrightBrowserTool
from cognitive_assistant.shared.telemetry.trace import set_trace_id


def test_playwright_tool_instantiation():
    """Verifica que PlaywrightBrowserTool se instancie con canal por defecto."""
    tool = PlaywrightBrowserTool()
    assert tool.channel == "msedge"
    assert tool.headless is True


def test_firecrawl_tool_instantiation():
    """Verifica que FirecrawlTool se inicialice correctamente."""
    tool = FirecrawlTool()
    assert tool._app is None or tool.api_key is not None


@pytest.mark.asyncio
async def test_firecrawl_local_fallback():
    """Verifica que FirecrawlTool sin API Key genere respuesta estructurada con trace_id."""
    from unittest.mock import AsyncMock, patch

    set_trace_id("test-web-trace-001")
    tool = FirecrawlTool()

    with patch("cognitive_assistant.shared.tools.web_browser.get_playwright_tool") as mock_get_pw:
        mock_pw = AsyncMock()
        mock_pw.fetch_page_content.return_value = {
            "title": "Example Domain",
            "content": "Contenido extraído mediante fallback local.",
            "status": "success",
            "trace_id": "test-web-trace-001",
        }
        mock_get_pw.return_value = mock_pw

        result = await tool.scrape_url("https://example.com")
        assert "trace_id" in result
        assert result["trace_id"] == "test-web-trace-001"
        assert "markdown" in result
        assert "Contenido extraído" in result["markdown"]

