from pathlib import Path
from typing import Optional, Tuple

from playwright.async_api import Page


async def upload_file(page: Page, file_path: Path) -> None:
    # Click or reveal file chooser then set files
    for trigger in (
        'input[type="file"]',
        'button[aria-label="Attach"]',
        'button[data-testid="upload-button"]',
    ):
        if await page.is_visible(trigger):
            if trigger.startswith('input'):
                await page.set_input_files('input[type="file"]', str(file_path))
                return
            else:
                chooser = page.wait_for_event("filechooser")
                await page.click(trigger)
                filechooser = await chooser
                await filechooser.set_files(str(file_path))
                return

    # Fallback: try direct input
    await page.set_input_files('input[type="file"]', str(file_path))


async def download_next(page: Page, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    with page.expect_download() as dl_info:
        # Attempt to click a likely download button
        for selector in (
            'a[download]',
            'button[aria-label="Download"]',
            'button[data-testid="download-button"]',
        ):
            if await page.is_visible(selector):
                await page.click(selector)
                break
    download = await dl_info.value
    path = target_dir / (download.suggested_filename or "copilot-download")
    await download.save_as(str(path))
    return path
