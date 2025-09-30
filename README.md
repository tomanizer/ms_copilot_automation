# MS365 Copilot Automation (Python + Playwright)

Minimal CLI to:
- Authenticate to MS365 Copilot (manual or scripted)
- Send prompts and read responses
- Upload a file and ask for a summary

## Requirements

- Python 3.10+
- Playwright browsers (`python -m playwright install chromium`)
- Access to Microsoft Copilot with valid credentials (username + password, optional TOTP secret)

## Quickstart

```bash
# 1) Create venv
python3 -m venv venv
source venv/bin/activate

# 2) Install deps and browsers
pip install -r requirements.txt
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
python -m src.cli.main --headed auth --manual
# A browser opens. Complete Microsoft login. Press Ctrl+C when done.

# 5) Chat (headless by default)
python -m src.cli.main chat "Say hello"

# 6) Upload + summarize to output/
mkdir -p output
python -m pip install python-docx --quiet
python - <<'PY'
from docx import Document
D=Document(); D.add_heading('Sample',0)
D.add_paragraph('Short test doc about productivity with AI assistants.')
D.save('sample.docx')
PY

python -m src.cli.main --output-dir output ask-with-file sample.docx \
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

## CLI

Global options (apply to all commands):
- `--headless/--headed`: Run browser headless or headed (default: headless)
- `--output-dir DIRECTORY`: Set output directory (created if missing)
- `--log-level [DEBUG|INFO|WARNING|ERROR]`: Control log verbosity

```bash
# Auth
python -m src.cli.main --headed auth --manual             # headed, manual (saves state periodically)
python -m src.cli.main auth --interactive                  # prompts for creds (username/password/TOTP)
python -m src.cli.main auth                                # non-interactive (env/keyring)

# Chat
python -m src.cli.main chat "Your prompt"                  # prints styled panel
python -m src.cli.main chat "Your prompt" --out output/resp.txt

# Upload + ask
python -m src.cli.main ask-with-file /path/doc.docx "Summarize" \
  --out output/summary.md --download
python -m src.cli.main --headed ask-with-file sample.docx "Summarize" \
  --download-dir output/downloads --download

# Download latest artifact from current chat
python -m src.cli.main download --timeout 90 --out output
```

## Notes
- Uses Playwright storage state at `playwright/auth/user.json` (ignored by git)
- Logs go to stdout; control via `--log-level` or `LOG_LEVEL` env var
- Default output dir is current working directory; use `--output-dir` for convenience
- Styled output via `rich` (panels, colors)
- Secrets stored via `keyring` land in your OS credential store (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- If keyring access is blocked, you can use `.keyring.json` as plaintext fallback (ignored by git)
- Regenerate Playwright auth state anytime with `python -m src.cli.main --headed auth --manual`
- For debugging UI flows, run with `--headed` or `PWDEBUG=1` to open the Playwright inspector
