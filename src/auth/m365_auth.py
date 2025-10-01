from playwright.async_api import BrowserContext, Page
from pyotp import TOTP

from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


async def _click_sign_in_if_present(page: Page) -> None:
    for locator in (
        'role=link[name="Sign in"]',
        'role=button[name="Sign in"]',
        "text=Sign in",
        'a:has-text("Sign in")',
        'button:has-text("Sign in")',
    ):
        try:
            if await page.is_visible(locator, timeout=2000):
                await page.click(locator)
                return
        except Exception:
            continue


async def _login_via_live(page: Page, username: str, password: str) -> bool:
    # Consumer Microsoft account (Hotmail/Outlook)
    await page.goto("https://login.live.com/")
    try:
        await page.wait_for_selector("#i0116", timeout=45000)
        await page.fill("#i0116", username)
        await page.click("#idSIButton9")
        await page.wait_for_selector("#i0118", timeout=45000)
        await page.fill("#i0118", password)
        await page.click("#idSIButton9")
        # Post-login prompts (Stay signed in?)
        try:
            if await page.is_visible("#idSIButton9", timeout=5000):
                await page.click("#idSIButton9")
        except Exception:
            pass
        await page.wait_for_load_state("networkidle")
        return True
    except Exception:
        return False


async def _login_via_generic(
    page: Page, username: str, password: str, mfa_secret: str | None
) -> bool:
    settings = get_settings()
    await page.goto(settings.copilot_url)
    await _click_sign_in_if_present(page)
    try:
        await page.wait_for_selector(
            'input[type="email"], input[name="loginfmt"], #i0116', timeout=45000
        )
        if await page.is_visible("#i0116"):
            await page.fill("#i0116", username)
        else:
            await page.fill('input[type="email"], input[name="loginfmt"]', username)
        for submit in (
            "#idSIButton9",
            'input[type="submit"]',
            'button[type="submit"]',
            'input[value="Next"]',
            'button:has-text("Next")',
        ):
            if await page.is_visible(submit):
                await page.click(submit)
                break
        await page.wait_for_selector('input[type="password"], #i0118', timeout=45000)
        if await page.is_visible("#i0118"):
            await page.fill("#i0118", password)
        else:
            await page.fill('input[type="password"]', password)
        for submit in (
            "#idSIButton9",
            'input[type="submit"]',
            'button[type="submit"]',
            'button:has-text("Sign in")',
            'input[value="Sign in"]',
        ):
            if await page.is_visible(submit):
                await page.click(submit)
                break
        if mfa_secret and await page.is_visible('input[name="otc"]', timeout=5000):
            otp = TOTP(mfa_secret).now()
            await page.fill('input[name="otc"]', otp)
            for submit in ('input[type="submit"]', 'button[type="submit"]'):
                if await page.is_visible(submit):
                    await page.click(submit)
                    break
        await page.wait_for_load_state("networkidle")
        return True
    except Exception:
        return False


async def perform_login(
    context: BrowserContext, username: str, password: str, mfa_secret: str | None = None
) -> None:
    """Login to MS365 (consumer or org) and persist storage state."""
    settings = get_settings()
    page: Page = await context.new_page()

    ok = await _login_via_live(page, username, password)
    if not ok:
        ok = await _login_via_generic(page, username, password, mfa_secret)

    if not ok:
        await page.close()
        raise RuntimeError("Login failed: selectors not found or flow changed")

    # Navigate to Copilot and persist state
    await page.goto(settings.copilot_url)
    await page.wait_for_load_state("networkidle")
    await context.storage_state(path=str(settings.storage_state_path))
    logger.info("Stored authentication state at %s", settings.storage_state_path)

    await page.close()
