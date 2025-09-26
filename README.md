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
python -c "import keyring; keyring.set_password('ms-copilot-automation','M365_PASSWORD','<your-password>')"
python -c "import keyring; keyring.set_password('ms-copilot-automation','M365_OTP_SECRET','<base32>')"  # optional

# 4) Manual auth (headed) to persist session
BROWSER_HEADLESS=false python -m src.cli.main auth --manual
# A browser opens. Complete Microsoft login. Leave it open ~10s, then Ctrl+C.

# 5) Chat (headless)
python -m src.cli.main chat "Say hello"

# 6) Upload + summarize
# Create a sample docx
python -m pip install python-docx --quiet
python - <<'PY'
from docx import Document
D=Document(); D.add_heading('Sample',0); D.add_paragraph('Short test doc about productivity with AI assistants.')
D.save('sample.docx')
PY

python -m src.cli.main ask-with-file sample.docx "Summarize into concise markdown bullets only." --out output/summary.md
```

## CLI
```bash
# Persist auth
python -m src.cli.main auth --manual               # headed, manual
python -m src.cli.main auth --interactive          # prompts for creds

# Chat
python -m src.cli.main chat "Your prompt" --out output/resp.txt

# Upload + ask
python -m src.cli.main ask-with-file /path/doc.docx "Summarize" --out output/summary.md
```

## Notes
- Uses Playwright storage state at `playwright/auth/user.json` (ignored by git)
- Logs go to stdout; control via `LOG_LEVEL` env var
- Default output dir is `./output` (add `OUTPUT_DIRECTORY=output` to `.env` if desired)
