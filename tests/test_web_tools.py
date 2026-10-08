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
    set_trace_id("test-web-trace-001")
    tool = FirecrawlTool()

    # Usar una URL mock o local para fallback
    result = await tool.scrape_url("http://localhost:8000/health")
    assert "trace_id" in result
    assert result["trace_id"] == "test-web-trace-001"
    assert "markdown" in result
