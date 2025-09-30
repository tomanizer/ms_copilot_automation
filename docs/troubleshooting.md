# Troubleshooting & FAQ

## Browser Launch Issues

- **Error:** `BrowserType.launch: Target page, context or browser has been closed`.
  - Ensure Playwright browsers are installed: `python -m playwright install chromium`.
  - Check for security prompts (especially on macOS) requesting permission to control the computer.
  - Try running with `--headed` to observe the UI.

- **Timeout waiting for Copilot UI**
  - Copilot may display cookies or consent banners. Run headed, dismiss prompts manually, and update `prepare_chat_ui` selectors if required.

## Authentication Problems

- **Missing credentials:** `RuntimeError: Missing credentials: set M365_USERNAME and M365_PASSWORD ...`
  - Confirm `.env` includes `M365_USERNAME`.
  - Store password via keyring (`python -m keyring set ...`) or `.keyring.json` fallback.

- **MFA prompts stall automation**
  - Provide `M365_OTP_SECRET` in keyring, or perform a manual headed login to refresh `playwright/auth/user.json`.

## Live Tests Hang

- Set `PWDEBUG=1` to use Playwright Inspector and watch where the script waits.
- Ensure `M365_COPILOT_E2E=1` is set and credentials/storage state are available.
- Copilot occasionally refuses downloads; the test skips when that happens.
- Disable the automatic Markdown instruction temporarily with `--no-force-markdown` or `COPILOT_FORCE_MARKDOWN=false` if you need to compare raw responses.

## CLI Tips

- Use `--headed` for manual observation; `--headless` is default.
- `PWDEBUG=1 ms-copilot ...` opens the inspector for a single command.
- Delete `playwright/auth/user.json` if the session becomes invalid.

## Config Changes Not Applied

- `get_settings()` is cached. Call `reset_settings_cache()` after changing environment variables in the same process.

## Logging & Debugging

- Set `LOG_LEVEL=DEBUG` or pass `--log-level DEBUG` to increase verbosity.
- Playwright tracing: set `PLAYWRIGHT_MAX_RETRIES=1` and `DEBUG=pw:api` for deeper logs.

## FAQ

**Q: Can I run this headlessly on a CI server?**
A: Yes, but you must supply a valid storage state and disable first-time login (e.g., run `auth --manual` locally and commit the state securely or fetch it from storage). Avoid embedding passwords in CI env vars unless necessary.

**Q: Does this support other browsers?**
A: The controller launches Chromium. Modify `CopilotController.start()` to use `playwright.firefox` or `playwright.webkit` if required.

**Q: Where are downloads saved?**
A: By default, the CLI writes to `./output`; override with `--output-dir` or the `OUTPUT_DIRECTORY` env var.

Still stuck? Open an issue with logs and steps to reproduce.
