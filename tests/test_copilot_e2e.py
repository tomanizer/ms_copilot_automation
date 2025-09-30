"""Live end-to-end checks against Microsoft Copilot.

These tests exercise the real Copilot experience and therefore require:

* ``M365_USERNAME`` and ``M365_PASSWORD`` (and optionally ``M365_OTP_SECRET``)
  to be set for an account that can access Microsoft Copilot.
* ``M365_COPILOT_E2E=1`` (or any truthy value) to opt-in to the live run.
* Stable network access plus the ability to launch a headed browser if desired.

They are marked with ``pytest.mark.copilot_e2e`` and skipped by default so that
normal CI runs remain fast and deterministic.
"""

from __future__ import annotations

import os
from pathlib import Path
from textwrap import dedent

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from src.automation.copilot_controller import CopilotController
from src.utils.config import get_settings


load_dotenv(dotenv_path=Path(".env"), override=False)


_raw_flag = os.getenv("M365_COPILOT_E2E", "")
LIVE_FLAG = _raw_flag.lower() in {"1", "true", "yes", "on"}


def _require_live_env():
    settings = get_settings()
    env_username = os.getenv("M365_USERNAME") or settings.username
    env_password = os.getenv("M365_PASSWORD") or settings.password
    storage_ready = settings.storage_state_path.exists()
    if env_username and not settings.username:
        settings.username = env_username
    if env_password and not settings.password:
        settings.password = env_password
    missing = []
    if not env_username and not storage_ready:
        missing.append("M365_USERNAME")
    if not env_password and not storage_ready:
        missing.append("M365_PASSWORD")
    if storage_ready and missing:
        missing = []
    return missing


skip_live = pytest.mark.skipif(
    not LIVE_FLAG,
    reason=(
        "Live Copilot E2E tests disabled. Set M365_COPILOT_E2E=1 (current value:"
        f" '{_raw_flag or 'unset'}')."
    ),
)


@pytest_asyncio.fixture(scope="module")
async def live_controller():
    missing = _require_live_env()
    if missing:
        hint = (
            "Populate .env with M365_USERNAME/M365_COPILOT_E2E and store sensitive "
            "values in keyring (python -m keyring set ms-copilot-automation …)."
        )
        pytest.skip("Missing required credentials: " + ", ".join(missing) + ". " + hint)

    controller = CopilotController()
    try:
        try:
            await controller.start()
        except Exception as exc:  # pragma: no cover - launch issues (missing browser?)
            await controller.close()
            pytest.skip(f"Playwright failed to launch Chromium: {exc}")
        await controller.ensure_authenticated()
        yield controller
    finally:
        await controller.close()


@skip_live
@pytest.mark.copilot_e2e
@pytest.mark.asyncio
async def test_copilot_chat_returns_content(live_controller: CopilotController):
    prompt = "Respond with a short friendly greeting for the Copilot smoke test."
    response = await live_controller.chat(prompt)

    assert response.strip(), "Chat response should not be empty"
    assert "greeting" not in response.lower() or len(response.split()) >= 3


@skip_live
@pytest.mark.copilot_e2e
@pytest.mark.asyncio
async def test_copilot_ask_with_file_reads_attachment(
    live_controller: CopilotController, tmp_path: Path
):
    sample = tmp_path / "sample.txt"
    sample.write_text(
        dedent(
            """
            This is a synthetic report for Copilot QA.
            Highlight three observations and summarise in 2 sentences.
            """
        ).strip()
    )

    prompt = "Summarise the attached report in two sentences."
    response = await live_controller.ask_with_file(sample, prompt)

    assert response.strip(), "File-based response should not be empty"


@skip_live
@pytest.mark.copilot_e2e
@pytest.mark.asyncio
async def test_copilot_can_provide_downloadable_artifact(
    live_controller: CopilotController, tmp_path: Path
):
    prompt = (
        "Create a small CSV file with three sample tasks and make it available as a download."
    )
    await live_controller.chat(prompt)

    try:
        artifact = await live_controller.download_response(tmp_path, timeout_ms=60000)
    except RuntimeError as exc:  # Copilot may decline to create downloads
        pytest.skip(f"Copilot did not provide a download this run: {exc}")

    assert artifact.exists()
    assert artifact.suffix in {".csv", ".xlsx", ".txt"}
