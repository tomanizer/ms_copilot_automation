from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from ..auth.m365_auth import perform_login
from ..utils.config import get_settings
from ..utils.logger import get_logger
from .chat import send_prompt as _send_prompt, read_response_text as _read_response_text
from .files import upload_file as _upload_file, download_next as _download_next
from .ui import prepare_chat_ui


logger = get_logger(__name__)


class CopilotController:
    def __init__(self) -> None:
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.settings = get_settings()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=self.settings.browser_headless)
        storage = str(self.settings.storage_state_path) if self.settings.storage_state_path.exists() else None
        self.context = await self.browser.new_context(storage_state=storage)
        self.page = await self.context.new_page()

    async def ensure_authenticated(self) -> None:
        if not self.context:
            raise RuntimeError("Controller not started")
        if not self.settings.storage_state_path.exists():
            logger.info("Performing first-time login")
            await perform_login(
                self.context,
                username=self.settings.username or "",
                password=self.settings.password or "",
                mfa_secret=self.settings.mfa_secret,
            )

    async def chat(self, prompt: str) -> str:
        await self.ensure_authenticated()
        assert self.page
        await self.page.goto(self.settings.copilot_url)
        await prepare_chat_ui(self.page)
        await _send_prompt(self.page, prompt)
        return await _read_response_text(self.page, exclude_text=prompt)

    async def ask_with_file(self, file_path: Path, prompt: str) -> str:
        await self.ensure_authenticated()
        assert self.page
        await self.page.goto(self.settings.copilot_url)
        await prepare_chat_ui(self.page)
        await _upload_file(self.page, file_path)
        await _send_prompt(self.page, prompt)
        return await _read_response_text(self.page, exclude_text=prompt)

    async def download_response(self, target_dir: Path, timeout_ms: int = 45000) -> Path:
        assert self.page
        logger.info("Starting download into %s", target_dir)
        try:
            path = await _download_next(self.page, target_dir, timeout_ms=timeout_ms)
            logger.info("Download completed: %s", path)
            return path
        except RuntimeError as exc:
            logger.warning("Download attempt failed: %s", exc)
            raise

    async def close(self) -> None:
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
