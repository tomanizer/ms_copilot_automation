import re
from html import unescape

from playwright.async_api import Page

from .constants import (
    CITATION_PATTERN,
    MESSAGE_SELECTORS,
    NETWORK_IDLE_TIMEOUT_MS,
    NOISY_PHRASES,
    POLL_INTERVAL_MS,
    RAW_MARKDOWN_SELECTORS,
    STATUS_PREFIXES,
)


async def send_prompt(page: Page, prompt: str) -> None:
    await page.fill('textarea, [role="textbox"]', prompt)
    for selector in (
        'button[aria-label="Send"]',
        'button[data-testid="send-button"]',
        'button[type="submit"]',
    ):
        if await page.is_visible(selector):
            await page.click(selector)
            return
    await page.keyboard.press("Enter")


async def _collect_texts(page: Page, selector: str) -> list[str]:
    texts: list[str] = []
    loc = page.locator(selector)
    try:
        count = await loc.count()
    except Exception:
        count = 0
    for i in range(max(0, count - 12), count):
        try:
            el = loc.nth(i)
            txt = await el.inner_text()
            if txt and txt.strip():
                texts.append(txt.strip())
        except Exception:
            continue
    return texts


async def get_last_message_text(page: Page) -> str | None:
    candidates: list[str] = []
    for selector in MESSAGE_SELECTORS:
        try:
            if await page.is_visible(selector, timeout=300):
                candidates.extend(await _collect_texts(page, selector))
        except Exception:
            continue
    filtered = _filter_candidates(candidates, None)
    return filtered[-1] if filtered else None


async def _extract_raw_markdown(page: Page) -> str | None:
    latest: str | None = None
    for selector in RAW_MARKDOWN_SELECTORS:
        try:
            locator = page.locator(selector)
            count = await locator.count()
        except Exception:
            continue
        if not count:
            continue
        for index in range(count):
            try:
                text = await locator.nth(index).text_content()
            except Exception:
                continue
            if text and text.strip():
                latest = text.strip()
        if latest:
            break
    return latest


def _filter_candidates(candidates: list[str], exclude_text: str | None) -> list[str]:
    """Filter out noise and duplicates from chat message candidates.

    :param candidates: List of candidate message texts
    :type candidates: list[str]
    :param exclude_text: Text to exclude from results (e.g., user's prompt)
    :type exclude_text: str | None
    :returns: Filtered list of unique, relevant messages
    :rtype: list[str]
    """
    seen = set()
    filtered: list[str] = []
    for t in candidates:
        if exclude_text and exclude_text.strip() in t:
            continue
        if any(t.startswith(pfx) for pfx in STATUS_PREFIXES):
            continue
        if any(phrase in t for phrase in NOISY_PHRASES):
            continue
        key = t.strip()
        if key and key not in seen:
            seen.add(key)
            filtered.append(key)
    return filtered


def _score(text: str) -> tuple[int, int]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    bullet_lines = sum(1 for ln in lines if ln.startswith(("- ", "* ", "• ")))
    has_heading = any(ln.startswith("#") or ln.endswith(":") for ln in lines[:3])
    score = 0
    if bullet_lines >= 2:
        score += 3
    elif bullet_lines == 1:
        score += 1
    if has_heading:
        score += 1
    score += min(len(text), 2000) // 200
    return score, len(text)


def _normalise_response(text: str) -> str:
    """Normalize Copilot response text into clean Markdown.

    :param text: Raw response text from Copilot
    :type text: str
    :returns: Cleaned and normalized Markdown text
    :rtype: str
    """
    # Unescape HTML entities
    text = unescape(text)

    # Remove citation patterns
    text = CITATION_PATTERN.sub("", text)

    # Remove carriage returns
    text = re.sub(r"\r", "", text)

    # Remove trailing whitespace from lines
    text = re.sub(r"[ \t]+\n", "\n", text)

    # Remove leading whitespace from lines
    text = re.sub(r"\n[ \t]+", "\n", text)

    # Remove leading whitespace from all lines
    text = re.sub(r"^[ \t]+", "", text, flags=re.MULTILINE)

    # Normalize horizontal rules (---)
    text = re.sub(r"(?:^|\n)\s*-{3,}\s*(?=\n|$)", "\n\n---\n\n", text)

    # Add newlines before headings
    text = re.sub(
        r"(?<!\n)(#{1,6}\s+[^\n]+)",
        lambda m: "\n\n" + m.group(1).strip(),
        text,
    )

    # Ensure proper spacing after horizontal rules before headings
    text = re.sub(
        r"(---)\s+(#{1,6}\s+[^\n]+)",
        lambda m: f"{m.group(1)}\n\n{m.group(2).strip()}",
        text,
    )

    # Add newlines before bullet points
    text = re.sub(r"(?<!\n)[ \t]+([-*•]\s)", r"\n\1", text)

    # Add newlines before numbered lists
    text = re.sub(r"(?<![\n-])[ \t]+(\d+\.\s)", r"\n\1", text)

    # Normalize multiple newlines to at most 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove "Copilot said" prefix
    text = re.sub(r"^copilot said\s*", "", text, flags=re.IGNORECASE)

    # Remove "Edit in a page" suffix
    text = re.sub(r"\n?Edit in a page\s*$", "", text, flags=re.IGNORECASE)

    return text.strip()


async def read_response_text(
    page: Page,
    timeout_ms: int | None = None,
    exclude_text: str | None = None,
    normalise: bool = True,
) -> str:
    """Read and extract response text from Copilot.

    :param page: The Playwright page instance
    :type page: Page
    :param timeout_ms: Maximum time to wait for response (uses NETWORK_IDLE_TIMEOUT_MS if None)
    :type timeout_ms: int | None
    :param exclude_text: Text to exclude from results
    :type exclude_text: str | None
    :param normalise: Whether to normalize the markdown
    :type normalise: bool
    :returns: The response text from Copilot
    :rtype: str
    """
    if timeout_ms is None:
        timeout_ms = NETWORK_IDLE_TIMEOUT_MS

    await page.wait_for_load_state("networkidle")

    interval_ms = POLL_INTERVAL_MS
    elapsed = 0
    last_best: str | None = None
    stable_ticks = 0

    while elapsed < timeout_ms:
        candidates: list[str] = []
        for selector in MESSAGE_SELECTORS:
            try:
                if await page.is_visible(selector, timeout=500):
                    candidates.extend(await _collect_texts(page, selector))
            except Exception:
                continue
        filtered = _filter_candidates(candidates, exclude_text)
        if filtered:
            best = max(filtered, key=_score)
            if last_best == best:
                stable_ticks += 1
            else:
                last_best = best
                stable_ticks = 0
            if stable_ticks >= 2:
                if not normalise:
                    raw = await _extract_raw_markdown(page)
                    if raw:
                        return raw
                return _normalise_response(last_best) if normalise else last_best
        await page.wait_for_timeout(interval_ms)
        elapsed += interval_ms

    if last_best:
        if not normalise:
            raw = await _extract_raw_markdown(page)
            if raw:
                return raw
        return _normalise_response(last_best) if normalise else last_best
    base = await get_last_message_text(page)
    if base:
        if not normalise:
            raw = await _extract_raw_markdown(page)
            if raw:
                return raw
        return _normalise_response(base) if normalise else base
    try:
        main = await page.inner_text("main")
        if exclude_text and exclude_text.strip() in main:
            main = main.replace(exclude_text, "").strip()
        if main:
            if not normalise:
                raw = await _extract_raw_markdown(page)
                if raw:
                    return raw
            return _normalise_response(main) if normalise else main
    except Exception:
        pass
    return ""
