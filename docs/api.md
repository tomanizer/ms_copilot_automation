# Python API Reference

The project exposes a small Python API intended for scripting and testing.

## `CopilotController`

Located at `src.automation.copilot_controller.CopilotController`.

### Lifecycle

```python
from src.automation.copilot_controller import CopilotController

async with CopilotController() as ctl:
    response = await ctl.chat("Summarise the latest release notes")
    print(response)
```

Use `async with` to ensure Playwright resources close cleanly. Alternatively, call `await controller.start()` and `await controller.close()` manually.

### Methods

- `start()` – Launch Playwright, create browser, context, and page.
- `ensure_authenticated()` – Verify login state. If storage state is missing, performs a scripted login using credentials from settings; raises if neither storage state nor credentials are available.
- `chat(prompt: str) -> str` – Navigate to Copilot, prepare the UI, send a prompt, and return the textual response.
- `ask_with_file(file_path: Path, prompt: str) -> str` – Upload a file before sending the prompt; returns the response text.
- `download_response(target_dir: Path, timeout_ms: int = 45000) -> Path` – Wait for the next downloadable artifact and save it into `target_dir`.
- `close()` – Dispose Playwright resources (page, context, browser, playwright manager).

Prompts are automatically decorated with a Markdown instruction when `settings.force_markdown_responses` is `True` (default). Disable via `COPILOT_FORCE_MARKDOWN=false` or the CLI flag `--no-force-markdown`.

### Settings

`CopilotController` pulls configuration via `get_settings()` (see below). You can reset cached settings between runs with `reset_settings_cache()`.

## `get_settings` / `Settings`

Defined in `src.utils.config`.

```python
from src.utils.config import get_settings, reset_settings_cache

settings = get_settings()
print(settings.copilot_url)

# Reset cached values after modifying env vars
reset_settings_cache()
```

Key fields:

- `username`, `password`, `mfa_secret`
- `copilot_url`
- `browser_headless`
- `storage_state_path`
- `output_directory`
- `force_markdown_responses`

Secrets are sourced from (in order): environment variables, `.keyring.json` (fallback), then OS keyring. Non-secret config respects environment overrides (`M365_COPILOT_URL`, `BROWSER_HEADLESS`, etc.).

## Helper Modules

- `src.automation.chat`: lower-level helpers for sending prompts, collecting Copilot messages, and scoring responses.
- `src.automation.files`: utilities to upload files and capture downloads.
- `src.automation.ui`: hides cookie banners and onboarding popups.
- `src.auth.m365_auth`: scripted Microsoft login flows for consumer and organisational accounts.

Each helper is designed for async Playwright usage.

## Testing Utilities

See the `tests/` directory for sample usage patterns, including stubbed Playwright objects for unit tests (`tests/test_copilot_controller.py`) and opt-in live tests (`tests/test_copilot_e2e.py`).
