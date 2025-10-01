from playwright.async_api import Page

from .constants import SELECTOR_WAIT_MS, UI_CLEANUP_SELECTORS


async def prepare_chat_ui(page: Page) -> None:
    # Try to accept cookies/permissions and close onboarding surfaces
    for sel in UI_CLEANUP_SELECTORS:
        try:
            if await page.is_visible(sel, timeout=SELECTOR_WAIT_MS):
                await page.click(sel)
        except Exception:
            continue
