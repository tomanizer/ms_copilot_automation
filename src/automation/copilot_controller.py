import asyncio
import re
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from ..auth.m365_auth import perform_login
from ..utils.config import get_settings
from ..utils.logger import get_logger
from .chat import read_response_text as _read_response_text
from .chat import send_prompt as _send_prompt
from .constants import LOGGED_IN_INDICATORS, MARKDOWN_INSTRUCTION, SIGN_IN_SELECTORS
from .files import download_next as _download_next
from .files import upload_file as _upload_file
from .ui import prepare_chat_ui

logger = get_logger(__name__)


class CopilotController:
    """Controller for interacting with MS365 Copilot through browser automation."""

    def __init__(self) -> None:
        self._playwright: Any = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.settings = get_settings()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, _exc_type, _exc, _tb):
        await self.close()

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=self.settings.browser_headless
        )
        storage = (
            str(self.settings.storage_state_path)
            if self.settings.storage_state_path.exists()
            else None
        )
        self.context = await self.browser.new_context(storage_state=storage)
        self.page = await self.context.new_page()

    async def _check_if_logged_in(self, page: Page) -> bool:
        """Check if the user is actually logged in to Copilot."""
        for attempt in range(2):
            try:
                for indicator in SIGN_IN_SELECTORS:
                    if await page.is_visible(indicator, timeout=2000):
                        logger.warning(
                            "Found sign-in indicator %s; session considered unauthenticated",
                            indicator,
                        )
                        return False

                sign_in_menu = page.get_by_role(
                    "menuitem", name=re.compile(r"sign in", re.IGNORECASE)
                )
                if await sign_in_menu.is_visible(timeout=2000):
                    logger.warning(
                        "Found sign-in menuitem locator; session considered unauthenticated"
                    )
                    return False

                for indicator in LOGGED_IN_INDICATORS:
                    if await page.is_visible(indicator, timeout=2000):
                        logger.debug("Found logged-in indicator %s", indicator)
                        return True

                profile_menu = page.get_by_role(
                    "menuitem", name=re.compile(r"^profile image", re.IGNORECASE)
                )
                if await profile_menu.is_visible(timeout=2000):
                    logger.debug("Found profile menu item (logged in)")
                    return True
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Authentication probe attempt %d failed: %s", attempt + 1, exc)

            if attempt == 0:
                logger.debug("Retrying authentication probe after short delay")
                await asyncio.sleep(0.5)

        logger.warning("Unable to confirm authenticated state; assuming existing session is valid")
        return True

    async def ensure_authenticated(self) -> None:
        if not self.context:
            raise RuntimeError("Controller not started")

        needs_login = False

        # Check if storage state file exists
        if not self.settings.storage_state_path.exists():
            logger.info("No storage state found - need to login")
            needs_login = True
        else:
            # Storage state exists, but verify it's actually valid
            logger.debug("Storage state exists, verifying authentication...")
            assert self.page
            await self.page.goto(self.settings.copilot_url)
            await self.page.wait_for_load_state("networkidle")

            if not await self._check_if_logged_in(self.page):
                logger.warning("Storage state exists but user not logged in - need fresh login")
                needs_login = True

        if needs_login:
            if not (self.settings.username and self.settings.password):
                raise RuntimeError(
                    "Missing credentials: set M365_USERNAME and M365_PASSWORD or provide an existing storage state"
                )
            logger.info("Performing login")
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
        final_prompt = self._decorate_prompt(prompt)
        await _send_prompt(self.page, final_prompt)
        return await _read_response_text(
            self.page, exclude_text=final_prompt, normalise=self.settings.normalize_markdown
        )

    async def ask_with_file(self, file_path: Path, prompt: str) -> str:
        await self.ensure_authenticated()
        assert self.page
        await self.page.goto(self.settings.copilot_url)
        await prepare_chat_ui(self.page)
        await _upload_file(self.page, file_path)
        final_prompt = self._decorate_prompt(prompt)
        await _send_prompt(self.page, final_prompt)
        return await _read_response_text(
            self.page, exclude_text=final_prompt, normalise=self.settings.normalize_markdown
        )

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

    def _decorate_prompt(self, prompt: str) -> str:
        """Decorate prompt with Markdown instruction if configured.

        :param prompt: The user's prompt
        :type prompt: str
        :returns: Decorated prompt with Markdown instructions
        :rtype: str
        """
        if not self.settings.force_markdown_responses:
            return prompt
        instruction = MARKDOWN_INSTRUCTION.strip()
        if instruction.lower() in prompt.lower():
            return prompt
        prompt = prompt.rstrip()
        if prompt:
            return f"{prompt}\n\n{instruction}"
        return instruction
