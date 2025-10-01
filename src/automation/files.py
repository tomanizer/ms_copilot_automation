import time
from pathlib import Path

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.exceptions import (
    DownloadTimeoutError,
    FileUploadError,
    FileValidationError,
    UIInteractionError,
)

from ..utils.logger import get_logger
from ..utils.retry import retry_async
from .constants import (
    ALLOWED_FILE_EXTENSIONS,
    DEFAULT_TIMEOUT_MS,
    DOWNLOAD_BUTTON_SELECTORS,
    EXPONENTIAL_BACKOFF,
    FILE_ATTACHMENT_MS,
    FILE_UPLOAD_BUTTON_SELECTOR,
    MAX_FILE_SIZE_BYTES,
    MAX_RETRIES,
    MENU_ANIMATION_MS,
    PLUS_BUTTON_SELECTOR,
    RETRY_DELAY_MS,
    SELECTOR_WAIT_MS,
)

logger = get_logger(__name__)


def validate_file(file_path: Path) -> None:
    """Validate a file before upload.

    :param file_path: Path to the file to validate
    :type file_path: Path
    :raises FileValidationError: If validation fails
    """
    if not file_path.exists():
        raise FileValidationError(f"File does not exist: {file_path}")

    if not file_path.is_file():
        raise FileValidationError(f"Path is not a file: {file_path}")

    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        raise FileValidationError(f"File too large: {size_mb:.1f}MB (max: {max_mb:.0f}MB)")

    if file_path.suffix.lower() not in ALLOWED_FILE_EXTENSIONS:
        raise FileValidationError(
            f"File type not allowed: {file_path.suffix} "
            f"(allowed: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))})"
        )


async def _click_with_retry(page: Page, test_id: str, description: str) -> None:
    """Click an element with retry logic for transient failures.

    :param page: The Playwright page instance
    :type page: Page
    :param test_id: The test ID of the element to click
    :type test_id: str
    :param description: Description for logging
    :type description: str
    :raises UIInteractionError: If click fails after retries
    """

    async def _do_click() -> None:
        try:
            element = page.get_by_test_id(test_id)
            await element.click()
            logger.debug("Clicked %s", description)
        except Exception as exc:
            raise UIInteractionError(f"Failed to click {description}: {exc}") from exc

    await retry_async(
        _do_click,
        max_retries=MAX_RETRIES,
        delay_ms=RETRY_DELAY_MS,
        exponential_backoff=EXPONENTIAL_BACKOFF,
        retry_on=(UIInteractionError, PlaywrightTimeoutError),
    )


async def upload_file(page: Page, file_path: Path) -> None:
    """Upload a file to Copilot with automatic retry on transient failures.

    The upload flow:
    1. Validate the file
    2. Click the + button to open the menu (with retry)
    3. Set up file chooser interception to avoid OS dialog
    4. Click the file upload button (triggers file chooser event, with retry)
    5. File chooser automatically selects our file

    :param page: The Playwright page instance
    :type page: Page
    :param file_path: Path to the file to upload
    :type file_path: Path
    :raises FileValidationError: If file validation fails
    :raises FileUploadError: If upload fails after retries
    """
    # Validate file first
    validate_file(file_path)

    logger.info("Starting file upload for %s", file_path)

    try:
        # Step 1: Click the + button to open menu (with retry)
        await _click_with_retry(
            page,
            PLUS_BUTTON_SELECTOR.split("=")[-1].strip('"]'),
            "+ button",
        )
        await page.wait_for_timeout(MENU_ANIMATION_MS)

        # Step 2 & 3: Set up file chooser listener and click upload button (with retry)
        async def _click_upload_button() -> None:
            async with page.expect_file_chooser() as fc_info:
                file_upload_button = page.get_by_test_id(
                    FILE_UPLOAD_BUTTON_SELECTOR.split("=")[-1].strip('"]')
                )
                await file_upload_button.click()
                logger.debug("Clicked file upload button")

            file_chooser = await fc_info.value
            await file_chooser.set_files(str(file_path))

        await retry_async(
            _click_upload_button,
            max_retries=MAX_RETRIES,
            delay_ms=RETRY_DELAY_MS,
            exponential_backoff=EXPONENTIAL_BACKOFF,
            retry_on=(Exception,),
        )

        logger.info("File uploaded successfully: %s", file_path)

        # Step 4: Wait for file to be attached
        await page.wait_for_timeout(FILE_ATTACHMENT_MS)
        logger.debug("Waiting for file attachment to complete")

    except FileValidationError:
        # Re-raise validation errors as-is
        raise
    except Exception as exc:
        logger.exception("Failed to upload file")
        raise FileUploadError(f"File upload failed: {exc}") from exc


async def download_next(page: Page, target_dir: Path, timeout_ms: int | None = None) -> Path:
    """Wait for the next download and persist it to target_dir.

    :param page: The Playwright page instance
    :type page: Page
    :param target_dir: Directory to save the download
    :type target_dir: Path
    :param timeout_ms: Maximum time to wait (uses DEFAULT_TIMEOUT_MS if None)
    :type timeout_ms: int | None
    :raises DownloadTimeoutError: If no download is offered within timeout
    :returns: Path to the downloaded file
    :rtype: Path
    """
    if timeout_ms is None:
        timeout_ms = DEFAULT_TIMEOUT_MS

    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Waiting for Copilot to provide a downloadable file (timeout=%ss)",
        timeout_ms / 1000,
    )

    try:
        async with page.expect_download(timeout=timeout_ms) as dl_info:
            clicked = False
            for selector in DOWNLOAD_BUTTON_SELECTORS:
                try:
                    if await page.is_visible(selector, timeout=SELECTOR_WAIT_MS):
                        await page.click(selector)
                        clicked = True
                        logger.debug("Clicked download trigger %s", selector)
                        break
                except Exception:
                    continue
            if not clicked:
                logger.debug(
                    "No explicit download trigger found; waiting for automatic download event"
                )
        download = await dl_info.value
    except PlaywrightTimeoutError as exc:
        raise DownloadTimeoutError(
            f"Timed out waiting for a downloadable artifact from Copilot "
            f"(timeout: {timeout_ms / 1000}s)"
        ) from exc

    suggested = download.suggested_filename or f"copilot-download-{int(time.time())}"
    destination = target_dir / suggested
    await download.save_as(str(destination))
    logger.info("Saved Copilot download to %s", destination)
    return destination
