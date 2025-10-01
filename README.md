# MS365 Copilot Automation (Python + Playwright)

[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Issues](https://img.shields.io/github/issues/tomanizer/ms_copilot_automation.svg)](https://github.com/tomanizer/ms_copilot_automation/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/tomanizer/ms_copilot_automation.svg)](https://github.com/tomanizer/ms_copilot_automation/pulls)
[![Last Commit](https://img.shields.io/github/last-commit/tomanizer/ms_copilot_automation.svg)](https://github.com/tomanizer/ms_copilot_automation/commits)

Minimal CLI to:
- Authenticate to MS365 Copilot (manual or scripted)
- Send prompts and read responses
- Upload a file and ask for a summary

### New: Automatic Prompt Splitting
- Long prompts are automatically split into ordered parts when exceeding input limits.
- Each part is labeled (e.g., `[Part 1/2]`) and Copilot is instructed to wait until the final part.
- On the final part, Copilot is instructed to process the full prompt as a single input.

## Requirements

- Python 3.10+
- Playwright browsers (`python -m playwright install chromium`)
- Access to Microsoft Copilot with valid credentials (username + password, optional TOTP secret)

## Quickstart

```bash
# 1) Create venv
python3 -m venv venv
source venv/bin/activate

# 2) Install deps, browsers, and register CLI
pip install -r requirements.txt
pip install -e .
python -m playwright install chromium

# 3) Set secrets
# .env (do not commit)
echo "M365_USERNAME=your-email@domain.com" >> .env
# Store password/TOTP securely. Preferred: OS keyring (macOS Keychain, etc.)
python - <<'PY'
import keyring
keyring.set_password('ms-copilot-automation','M365_PASSWORD','<your-password>')
# Optional TOTP secret (base32)
# keyring.set_password('ms-copilot-automation','M365_OTP_SECRET','<base32>')
PY
# Alternate fallback: create `.keyring.json` with the same keys if keyring is unavailable
# echo '{"M365_PASSWORD": "...", "M365_OTP_SECRET": "..."}' > .keyring.json

# 4) Manual auth (headed) to persist session (saves state every few seconds)
ms-copilot --headed auth --manual
# A browser opens. Complete Microsoft login. Press Ctrl+C when done.

# 5) Chat (headless by default)
ms-copilot chat "Say hello"

# 6) Upload + summarize to output/
mkdir -p output
python -m pip install python-docx --quiet
python - <<'PY'
from docx import Document
D=Document(); D.add_heading('Sample',0)
D.add_paragraph('Short test doc about productivity with AI assistants.')
D.save('sample.docx')
PY

ms-copilot --output-dir output ask-with-file sample.docx \
  "Summarize into concise markdown bullets only." --out output/summary.md --download

# 7) Run tests (optional)
PYTHONPATH=$(pwd) pytest -q

# Optional: run live E2E suite (requires credentials, set M365_COPILOT_E2E=1)
M365_COPILOT_E2E=1 PYTHONPATH=$(pwd) pytest -m copilot_e2e
```

## Environment Variables

| Name | Purpose | Default |
| --- | --- | --- |
| `M365_USERNAME` | MS account email (required) | `None` |
| `M365_PASSWORD` | Password (read from keyring or `.keyring.json`) | `None` |
| `M365_OTP_SECRET` | Optional TOTP secret for MFA | `None` |
| `M365_COPILOT_URL` | Copilot endpoint | `https://copilot.microsoft.com` |
| `M365_COPILOT_E2E` | Opt-in flag for live tests | disabled |
| `BROWSER_HEADLESS` | Force headless/headed (`true`/`false`) | `true` |
| `OUTPUT_DIRECTORY` | Default output dir for artifacts | `./output` |
| `COPILOT_FORCE_MARKDOWN` | Append instruction so Copilot replies in Markdown (`true`/`false`) | `true` |
| `COPILOT_NORMALIZE_MARKDOWN` | Post-process Copilot output into tidy Markdown (`true`/`false`) | `true` |
| `COPILOT_MAX_PROMPT_CHARS` | Max characters per prompt before auto-splitting | `10000` |

## CLI

Global options (apply to all commands):
- `--headless/--headed`: Run browser headless or headed (default: headless)
- `--output-dir DIRECTORY`: Set output directory (created if missing)
- `--force-markdown/--no-force-markdown`: Toggle automatic Markdown instruction in prompts
- `--normalize-markdown/--raw-markdown`: Choose whether responses are normalised or left verbatim
- `--log-level [DEBUG|INFO|WARNING|ERROR]`: Control log verbosity
 - `--max-prompt-chars INTEGER`: Max characters per message before auto-splitting

```bash
# Auth
ms-copilot --headed auth --manual             # headed, manual (saves state periodically)
ms-copilot auth --interactive                  # prompts for creds (username/password/TOTP)
ms-copilot auth                                # non-interactive (env/keyring)

# Chat
ms-copilot chat "Your prompt"                  # prints styled panel
ms-copilot chat "Your prompt" --out output/resp.txt

# Upload + ask
ms-copilot ask-with-file /path/doc.docx "Summarize" \
  --out output/summary.md --download
ms-copilot --headed ask-with-file sample.docx "Summarize" \
  --download-dir output/downloads --download

# Download latest artifact from current chat
ms-copilot download --timeout 90 --out output
```

## Notes
- Uses Playwright storage state at `playwright/auth/user.json` (ignored by git)
- Logs go to stdout; control via `--log-level` or `LOG_LEVEL` env var
- Default output dir is current working directory; use `--output-dir` for convenience
- Styled output via `rich` (panels, colors)
- Secrets stored via `keyring` land in your OS credential store (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- If keyring access is blocked, you can use `.keyring.json` as plaintext fallback (ignored by git)
- Regenerate Playwright auth state anytime with `ms-copilot --headed auth --manual`
- For debugging UI flows, run with `--headed` or `PWDEBUG=1` to open the Playwright inspector
