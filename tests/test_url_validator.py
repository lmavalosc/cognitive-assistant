import pytest
from cognitive_assistant.shared.tools.url_validator import validate_outbound_url
from cognitive_assistant.shared.tools.web_browser import PlaywrightBrowserTool, FirecrawlTool


def test_url_validator_rejects_non_http_schemes():
    """Verifica que se bloqueen esquemas file://, ftp://, gopher://."""
    bad_schemes = [
        "file:///etc/passwd",
        "file:///C:/Windows/win.ini",
        "ftp://ftp.ejemplo.com/archivo.txt",
        "gopher://gopher.floodgap.com",
    ]
    for url in bad_schemes:
        with pytest.raises(ValueError) as exc_info:
            validate_outbound_url(url)
        assert "esquema no permitido" in str(exc_info.value).lower()


def test_url_validator_rejects_private_and_loopback_ips():
    """Verifica que se bloqueen destinos locales, privados y metadatos cloud (SSRF)."""
    blocked_urls = [
        "http://localhost:8000/api",
        "http://127.0.0.1:5432",
        "http://169.254.169.254/latest/meta-data",
        "http://10.0.0.1/admin",
        "http://192.168.1.1/router",
        "http://metadata.google.internal/computeMetadata/v1/",
    ]
    for url in blocked_urls:
        with pytest.raises(ValueError) as exc_info:
            validate_outbound_url(url)
        assert (
            "anti-ssrf" in str(exc_info.value).lower()
            or "red interna" in str(exc_info.value).lower()
            or "restringida" in str(exc_info.value).lower()
        )


@pytest.mark.asyncio
async def test_playwright_tool_aborts_on_ssrf():
    """Verifica que Playwright aborte de inmediato ante un destino de metadatos cloud sin navegar."""
    tool = PlaywrightBrowserTool()
    with pytest.raises(ValueError) as exc_info:
        await tool.fetch_page_content("http://169.254.169.254/latest/meta-data")
    assert "anti-ssrf" in str(exc_info.value).lower() or "restringida" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_firecrawl_tool_aborts_on_ssrf():
    """Verifica que Firecrawl aborte de inmediato ante un destino privado sin navegar."""
    tool = FirecrawlTool()
    with pytest.raises(ValueError) as exc_info:
        await tool.scrape_url("http://127.0.0.1:8000/secret")
    assert "anti-ssrf" in str(exc_info.value).lower() or "restringida" in str(exc_info.value).lower()
