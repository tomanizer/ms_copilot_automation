from playwright.async_api import Page


async def prepare_chat_ui(page: Page) -> None:
    # Try to accept cookies/permissions and close onboarding surfaces
    candidates = (
        'button:has-text("Accept all")',
        'button:has-text("Accept")',
        'button:has-text("Got it")',
        'button:has-text("Continue")',
        'button:has-text("Allow")',
        'button:has-text("OK")',
        'button[aria-label="Close"]',
        'button:has-text("Not now")',
    )
    for sel in candidates:
        try:
            if await page.is_visible(sel, timeout=500):
                await page.click(sel)
        except Exception:
            continue
