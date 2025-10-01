from __future__ import annotations

from .logger import get_logger

logger = get_logger(__name__)


def _split_by_words(text: str, max_len: int) -> list[str]:
    """Split text into chunks not exceeding max_len, preserving word boundaries.

    If a single word exceeds max_len, it is hard-split.
    """
    if max_len <= 0:
        return [text]
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    def flush() -> None:
        nonlocal current, current_len
        if current:
            chunks.append(" ".join(current))
            current = []
            current_len = 0

    for word in words:
        if len(word) > max_len:
            flush()
            start = 0
            while start < len(word):
                end = min(start + max_len, len(word))
                chunks.append(word[start:end])
                start = end
            continue
        projected = len(word) if not current else current_len + 1 + len(word)
        if projected <= max_len:
            current.append(word)
            current_len = projected
        else:
            flush()
            current.append(word)
            current_len = len(word)
    flush()
    return chunks if chunks else ([text] if text else [])


def build_copilot_chunk_messages(
    text: str,
    max_prompt_chars: int,
    final_instruction: str | None = None,
) -> list[str]:
    """Build Copilot-ready messages with part headers within the character limit.

    The function splits the input ``text`` into multiple messages when it exceeds
    ``max_prompt_chars``. Each message includes a "Part i/N" header. Non-final
    parts instruct Copilot not to respond yet; the final part instructs it to
    process all parts together. If ``final_instruction`` is provided, it is
    appended to the final part only.

    :param text: The full prompt text
    :param max_prompt_chars: Maximum characters allowed per message
    :param final_instruction: Optional instruction to append to the final part
    :returns: List of messages to send in order
    :rtype: list[str]
    """
    if max_prompt_chars <= 0 or len(text) <= max_prompt_chars:
        # Single message path. Include final_instruction if provided.
        if final_instruction and final_instruction.strip():
            base = text.rstrip()
            if base:
                return [f"{base}\n\n{final_instruction.strip()}"]
            return [final_instruction.strip()]
        return [text]

    # Reserve a conservative header budget so each message stays under the limit
    # even after we include "Part i/N" and short guidance lines.
    header_budget = 128
    payload_max = max(1, max_prompt_chars - header_budget)

    payload_chunks = _split_by_words(text, payload_max)
    total = len(payload_chunks)
    if total <= 1:
        if final_instruction and final_instruction.strip():
            base = text.rstrip()
            if base:
                return [f"{base}\n\n{final_instruction.strip()}"]
            return [final_instruction.strip()]
        return [text]

    messages: list[str] = []
    for idx, chunk in enumerate(payload_chunks, start=1):
        is_final = idx == total
        if is_final:
            header = f"[Part {idx}/{total} - Final]"
            tail_lines: list[str] = [
                "Now process all parts above as a single prompt.",
            ]
            if final_instruction and final_instruction.strip():
                tail_lines.append(final_instruction.strip())
        else:
            header = f"[Part {idx}/{total}]"
            tail_lines = [
                f"Do not respond yet. Wait until you receive Part {total}/{total}.",
            ]

        message = "\n".join([header, chunk.strip(), *tail_lines]).strip()
        if len(message) > max_prompt_chars:
            # As a last resort, hard-trim to respect platform limits.
            logger.debug(
                "Chunk message length %d exceeds max %d; trimming",
                len(message),
                max_prompt_chars,
            )
            message = message[:max_prompt_chars]
        messages.append(message)
    return messages
