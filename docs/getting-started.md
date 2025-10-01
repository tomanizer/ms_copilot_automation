# Getting Started

This quick guide walks you through installing dependencies, configuring credentials, and taking your first steps with the CLI.

## Prerequisites

- Python 3.10 or later
- Microsoft 365 Copilot access with a valid user account
- Chromium downloaded via Playwright (`python -m playwright install chromium`)

## Installation

```bash
# Clone the repository
git clone https://github.com/tomanizer/ms_copilot_automation.git
cd ms_copilot_automation

# Create and activate the virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies, package, and Playwright browsers
pip install -r requirements.txt
pip install -e .
python -m playwright install chromium
```

## Configure Secrets

1. Create a `.env` file (ignored by git) to store your Copilot username and optional settings:

   ```bash
   echo "M365_USERNAME=your-email@domain.com" >> .env
   # Optional convenience flags
   # echo "M365_COPILOT_URL=https://copilot.microsoft.com" >> .env
   # echo "M365_COPILOT_E2E=1" >> .env  # only if you plan to run live tests
   # echo "COPILOT_FORCE_MARKDOWN=false" >> .env  # disable automatic markdown instruction
   # echo "COPILOT_NORMALIZE_MARKDOWN=false" >> .env  # keep Copilot response unmodified
   # echo "COPILOT_MAX_PROMPT_CHARS=10000" >> .env  # override default split threshold
   ```

2. Store your password (and optional TOTP secret) securely:

   ```bash
   python - <<'PY'
   import keyring
   keyring.set_password('ms-copilot-automation', 'M365_PASSWORD', '<your-password>')
   # Optional:
   # keyring.set_password('ms-copilot-automation', 'M365_OTP_SECRET', '<base32-secret>')
   PY
   ```

   *Fallback:* if the OS keyring is unavailable, create `.keyring.json` with `M365_PASSWORD` and `M365_OTP_SECRET`. This file stays plaintext and should never be committed.

## Authenticate

Run the manual authentication flow once to save a storage state:

```bash
ms-copilot --headed auth --manual
```

A browser window opens. Complete the Microsoft login. Press `Ctrl+C` in the terminal after you see Copilot ready; the automation saves state at regular intervals to `playwright/auth/user.json`.

## First Chat

```bash
ms-copilot chat "Say hello in three words"
```

## Upload + Summarise

```bash
ms-copilot --output-dir output ask-with-file docs/report.docx \
  "Summarise this document into bullet points" --download
```

## Run Tests

```bash
PYTHONPATH=$(pwd) pytest
```

(Optional) to exercise live Copilot flows, ensure the storage state or credentials are ready and run:

```bash
M365_COPILOT_E2E=1 PYTHONPATH=$(pwd) pytest -m copilot_e2e
```

You're ready to explore the rest of the documentation:

- [Detailed CLI usage](cli.md)
- [Python API reference](api.md)
- [Contributor guidelines](contributing.md)
- [Troubleshooting tips](troubleshooting.md)
