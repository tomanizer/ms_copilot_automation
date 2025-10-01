# Command Line Usage

The CLI is the primary interface for automating Microsoft Copilot interactions. After installing the project (`pip install -e .`), a console script named `ms-copilot` becomes available.

## Global Options

| Option | Description | Default |
| --- | --- | --- |
| `--headless/--headed` | Switch browser mode. | Headless |
| `--output-dir PATH` | Override the default output directory (`OUTPUT_DIRECTORY` env). | `./output` |
| `--force-markdown/--no-force-markdown` | Toggle automatic Markdown instruction appended to prompts. | Config value |
| `--normalize-markdown/--raw-markdown` | Post-process Copilot output or leave the raw response. | Config value |
| `--log-level LEVEL` | Override logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). | `INFO` |
| `--max-prompt-chars INTEGER` | Maximum characters per message before automatic splitting. | Config value |

Global options must appear before the subcommand. Example:

```bash
ms-copilot --headed --log-level DEBUG chat "Create a haiku about coffee"
```

## Authentication

```bash
ms-copilot auth [OPTIONS]
```

- `--manual`: open a headed browser and keep saving storage state until you interrupt (best for initial setup).
- `--interactive`: prompt for username/password/TOTP at the terminal, then perform an automated login.

Examples:

```bash
ms-copilot --headed auth --manual
ms-copilot auth --interactive
ms-copilot auth  # uses env/keyring credentials
```

## Chat

Send a prompt and print or save the response. If a prompt exceeds the configured character limit, it is split into ordered parts:

- Non-final parts include a header like `[Part 1/3]` and instruct Copilot to wait.
- The final part uses `[Part 3/3 - Final]` and instructs Copilot to process all parts together.

```bash
ms-copilot chat "Draft a short status update"
ms-copilot chat "Draft a short status update" --out output/status.md
```

## Ask With File

Upload a file, send a prompt, optionally download generated artifacts.

```bash
ms-copilot ask-with-file /path/to/report.pdf "Summarise key risks"
ms-copilot ask-with-file report.docx "Summarise" --out output/summary.txt
ms-copilot ask-with-file slides.pptx "Draft speaker notes" --download --download-dir output/artifacts
```

## Download

Wait for Copilot to offer the next downloadable artifact in the current chat.

```bash
ms-copilot download --timeout 90 --out output/downloads
```

## Environment Variables

The CLI pulls additional configuration from environment variables or `.env`:

- `M365_USERNAME`, `M365_PASSWORD`, `M365_OTP_SECRET`
- `M365_COPILOT_URL`
- `BROWSER_HEADLESS`
- `OUTPUT_DIRECTORY`
- `COPILOT_NORMALIZE_MARKDOWN`
- `COPILOT_FORCE_MARKDOWN`
- `COPILOT_MAX_PROMPT_CHARS`

See the [Environment Reference](getting-started.md#configure-secrets) for full details.

## Tips

- Use `ms-copilot --headed ...` to watch the browser and debug selectors.
- Set `PWDEBUG=1` to launch the Playwright Inspector for step-by-step tracing.
- Delete `playwright/auth/user.json` if you need a fresh login.
