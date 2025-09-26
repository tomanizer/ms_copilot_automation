# MS365 Copilot Automation — MVP Spec (Python + Playwright)

## Scope (MVP)
- Authenticate to MS365 Copilot (SSO + optional TOTP)
- Send a prompt to web chat and read full response
- Upload a file (e.g., .docx) and reference it in a prompt
- Download response artifact (e.g., .md) when provided
- Run headless/non-headless; log everything (no prints)

## Minimal Architecture
```
ms_copilot_automation/
├── src/
│   ├── auth/
│   │   └── m365_auth.py          # Login + storage_state
│   ├── automation/
│   │   ├── copilot_controller.py # Orchestrate chat/upload/download
│   │   ├── chat.py               # Prompt send + response read
│   │   └── files.py              # Upload/download helpers
│   ├── cli/
│   │   └── main.py               # CLI commands
│   └── utils/
│       ├── config.py             # Pydantic settings + dotenv/keyring
│       └── logger.py             # Logging setup
├── tests/
│   └── test_smoke.py             # Happy-path e2e
├── requirements.txt
└── README.md
```

## Key Flows
1) Auth
   - Navigate to `M365_COPILOT_URL`
   - Fill username/password; handle TOTP if `M365_OTP_SECRET` set
   - Save Playwright `storage_state` for reuse

2) Chat
   - Open chat page
   - Type prompt, send
   - Wait until response complete; return text

3) Upload
   - Trigger file chooser; set file path
   - Confirm attachment visible in chat

4) Download
   - Wait for downloadable item/link
   - Initiate download; save to `OUTPUT_DIRECTORY`

## CLI (Minimal)
```
ms-copilot auth                # uses env/keyring; prompts if --interactive
ms-copilot chat "Prompt..."    --out out.txt
ms-copilot upload document.docx
ms-copilot ask-with-file document.docx "Summarize" --out summary.md
```

## Settings & Secrets
- `.env` for local; system keyring for sensitive values
- Pydantic `Settings` loads: `M365_USERNAME`, `M365_PASSWORD`, `M365_OTP_SECRET`, `M365_COPILOT_URL`, `OUTPUT_DIRECTORY`, `BROWSER_HEADLESS`
- Never put secrets in CLI args by default; support `--interactive`

## Dependencies (requirements.txt)
```
playwright>=1.40.0
pydantic>=2.0.0
click>=8.0.0
python-dotenv>=1.0.0
keyring>=24.0.0
pyotp>=2.8.0
aiofiles>=23.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

## Implementation Notes
- Use `asyncio` APIs from Playwright
- Use stable selectors; prefer `aria-label`/`data-testid`
- Wrap waits with timeouts + single retry
- Central logger; no prints

## Done Criteria (MVP)
- `ms-copilot auth` persists session
- `ms-copilot chat "x"` returns response text to file/stdout
- `ask-with-file` uploads `.docx`, gets summary, downloads `.md`
- Works headless on CI and locally in UI mode

