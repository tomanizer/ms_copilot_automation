# MS365 Copilot Automation (Python + Playwright)

Minimal CLI to:
- Authenticate to MS365 Copilot (manual or scripted)
- Send prompts and read responses
- Upload a file and ask for a summary

## Quickstart

```bash
# 1) Create venv
python3 -m venv venv
source venv/bin/activate

# 2) Install deps and browsers
pip install -r requirements.txt
python -m playwright install

# 3) Set secrets (recommended: keyring + .env for username)
# .env (do not commit)
echo "M365_USERNAME=your-email@domain.com" >> .env
# Optional: set password and otp in keychain
python - <<'PY'
import keyring
keyring.set_password('ms-copilot-automation','M365_PASSWORD','<your-password>')
# Optional TOTP secret (base32)
# keyring.set_password('ms-copilot-automation','M365_OTP_SECRET','<base32>')
PY

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

python -m src.cli.main --output-dir output ask-with-file sample.docx "Summarize into concise markdown bullets only." --out output/summary.md
```

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
python -m src.cli.main ask-with-file /path/doc.docx "Summarize" --out output/summary.md
python -m src.cli.main --headed ask-with-file sample.docx "Summarize" --out output/summary.md

# Upload only (smoke)
python -m src.cli.main upload /path/doc.docx
```

## Notes
- Uses Playwright storage state at `playwright/auth/user.json` (ignored by git)
- Logs go to stdout; control via `--log-level` or `LOG_LEVEL` env var
- Default output dir is current working directory; use `--output-dir` for convenience
- Styled output via `rich` (panels, colors)
