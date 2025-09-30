import asyncio
from pathlib import Path

import pytest

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.automation import files


class _DummyDownload:
    def __init__(self, suggested="copilot.md") -> None:
        self.suggested_filename = suggested
        self.saved_to: Path | None = None

    async def save_as(self, destination: str) -> None:
        path = Path(destination)
        path.write_text("dummy")
        self.saved_to = path


class _DummyDownloadInfo:
    def __init__(self, download: _DummyDownload) -> None:
        self._download = download

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    @property
    def value(self):
        async def _inner():
            return self._download

        return _inner()


class _DummyPage:
    def __init__(self, download: _DummyDownload, visible=True, timeout=False) -> None:
        self._download = download
        self._visible = visible
        self.clicks: list[str] = []
        self._timeout = timeout

    async def is_visible(self, selector: str, timeout: int = 0):
        return self._visible

    async def click(self, selector: str):
        self.clicks.append(selector)

    def expect_download(self, timeout: int = 0):
        if self._timeout:
            raise PlaywrightTimeoutError("no download")
        return _DummyDownloadInfo(self._download)


@pytest.mark.asyncio
async def test_download_next_saves_file(tmp_path):
    download = _DummyDownload("report.md")
    page = _DummyPage(download)

    target = tmp_path / "artifacts"
    result = await files.download_next(page, target)

    assert result == target / "report.md"
    assert download.saved_to == result
    assert result.exists()
    assert page.clicks, "Should click one of the download triggers"


@pytest.mark.asyncio
async def test_download_next_times_out(tmp_path):
    download = _DummyDownload()
    page = _DummyPage(download, timeout=True)

    target = tmp_path / "artifacts"
    with pytest.raises(RuntimeError) as exc:
        await files.download_next(page, target, timeout_ms=100)

    assert "Timed out" in str(exc.value)
