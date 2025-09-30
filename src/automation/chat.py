import re
from html import unescape
from typing import Optional, List, Tuple

from playwright.async_api import Page


MESSAGE_SELECTORS = (
    'div[role="article"]',
    'div.chat-response',
    'div[data-content="message"]',
    'div[aria-live="polite"]',
    'div[role="dialog"] article',
    '[data-testid="message"]',
)

CITATION_PATTERN = re.compile(r"\[_\{\{\{CITATION\{\{\{_?\d+\{\]\([^)]+\)")


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


async def _collect_texts(page: Page, selector: str) -> List[str]:
    texts: List[str] = []
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


async def get_last_message_text(page: Page) -> Optional[str]:
    candidates: List[str] = []
    for selector in MESSAGE_SELECTORS:
        try:
            if await page.is_visible(selector, timeout=300):
                candidates.extend(await _collect_texts(page, selector))
        except Exception:
            continue
    filtered = _filter_candidates(candidates, None)
    return filtered[-1] if filtered else None


def _filter_candidates(candidates: List[str], exclude_text: Optional[str]) -> List[str]:
    status_prefixes = ("You said", "Uploading file", "Uploaded file", "Working on it")
    noisy_phrases = (
        "Nice to see you",
        "Copilot may make mistakes",
        "Your conversations are personalised",
        "Quick response",
        "Create an image",
        "Write a first draft",
        "Improve writing",
        "Design a logo",
        "Write a joke",
        "Rewrite a classic",
        "Draft an email",
        "Take a personality quiz",
        "Predict the future",
        "Improve communication",
    )
    seen = set()
    filtered: List[str] = []
    for t in candidates:
        if exclude_text and exclude_text.strip() in t:
            continue
        if any(t.startswith(pfx) for pfx in status_prefixes):
            continue
        if any(phrase in t for phrase in noisy_phrases):
            continue
        key = t.strip()
        if key and key not in seen:
            seen.add(key)
            filtered.append(key)
    return filtered


def _score(text: str) -> Tuple[int, int]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    bullet_lines = sum(1 for ln in lines if ln.startswith(('- ', '* ', '• ')))
    has_heading = any(ln.startswith('#') or ln.endswith(':') for ln in lines[:3])
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
    text = unescape(text)
    text = CITATION_PATTERN.sub("", text)
    text = re.sub(r"\r", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"^[ \t]+", "", text, flags=re.MULTILINE)
    text = re.sub(r"(?:^|\n)\s*-{3,}\s*(?=\n|$)", "\n\n---\n\n", text)
    text = re.sub(
        r"(?<!\n)(#{1,6}\s+[^\n]+)",
        lambda m: "\n\n" + m.group(1).strip(),
        text,
    )
    text = re.sub(
        r"(---)\s+(#{1,6}\s+[^\n]+)",
        lambda m: f"{m.group(1)}\n\n{m.group(2).strip()}",
        text,
    )
    text = re.sub(r"(?<!\n)[ \t]+([-*•]\s)", r"\n\1", text)
    text = re.sub(r"(?<![\n-])[ \t]+(\d+\.\s)", r"\n\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def read_response_text(page: Page, timeout_ms: int = 90000, exclude_text: Optional[str] = None) -> str:
    await page.wait_for_load_state("networkidle")

    interval_ms = 1000
    elapsed = 0
    last_best: Optional[str] = None
    stable_ticks = 0

    while elapsed < timeout_ms:
        candidates: List[str] = []
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
                return _normalise_response(last_best)
        await page.wait_for_timeout(interval_ms)
        elapsed += interval_ms

    if last_best:
        return _normalise_response(last_best)
    base = await get_last_message_text(page)
    if base:
        return _normalise_response(base)
    try:
        main = await page.inner_text("main")
        if exclude_text and exclude_text.strip() in main:
            main = main.replace(exclude_text, "").strip()
        if main:
            return _normalise_response(main)
    except Exception:
        pass
    return ""
