import time
from pathlib import Path

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from ..utils.logger import get_logger


logger = get_logger(__name__)


async def upload_file(page: Page, file_path: Path) -> None:
    # Click or reveal file chooser then set files
    for trigger in (
        'input[type="file"]',
        'button[aria-label="Attach"]',
        'button[data-testid="upload-button"]',
    ):
        try:
            if await page.is_visible(trigger):
                if trigger.startswith('input'):
                    await page.set_input_files('input[type="file"]', str(file_path))
                    return
                chooser = page.wait_for_event("filechooser")
                await page.click(trigger)
                filechooser = await chooser
                await filechooser.set_files(str(file_path))
                return
        except Exception:
            continue

    # Fallback: try direct input
    await page.set_input_files('input[type="file"]', str(file_path))


async def download_next(page: Page, target_dir: Path, timeout_ms: int = 45000) -> Path:
    """Wait for the next download and persist it to ``target_dir``.

    Raises ``RuntimeError`` if no download is offered within ``timeout_ms``.
    """

    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Waiting for Copilot to provide a downloadable file (timeout=%ss)", timeout_ms / 1000)
    try:
        async with page.expect_download(timeout=timeout_ms) as dl_info:
            clicked = False
            for selector in (
                'a[download]',
                'button[aria-label="Download"]',
                'button[data-testid="download-button"]',
                'button:has-text("Download")',
            ):
                try:
                    if await page.is_visible(selector, timeout=500):
                        await page.click(selector)
                        clicked = True
                        logger.debug("Clicked download trigger %s", selector)
                        break
                except Exception:
                    continue
            if not clicked:
                logger.debug("No explicit download trigger found; waiting for automatic download event")
        download = await dl_info.value
    except PlaywrightTimeoutError as exc:
        raise RuntimeError("Timed out waiting for a downloadable artifact from Copilot") from exc

    suggested = download.suggested_filename or f"copilot-download-{int(time.time())}"
    destination = target_dir / suggested
    await download.save_as(str(destination))
    logger.info("Saved Copilot download to %s", destination)
    return destination
