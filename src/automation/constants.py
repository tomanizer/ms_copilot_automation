"""Constants used across the automation modules.

This module centralizes all magic values, selectors, and configuration
constants to make them easier to maintain and update.
"""

import re

# ============================================================================
# Timeout Constants (in milliseconds)
# ============================================================================

DEFAULT_TIMEOUT_MS = 45000  # 45 seconds
NETWORK_IDLE_TIMEOUT_MS = 90000  # 90 seconds
POLL_INTERVAL_MS = 1000  # 1 second
SELECTOR_WAIT_MS = 500  # 0.5 seconds
MENU_ANIMATION_MS = 800  # 0.8 seconds
FILE_ATTACHMENT_MS = 1500  # 1.5 seconds

# ============================================================================
# Prompt Constants
# ============================================================================

DEFAULT_MAX_PROMPT_CHARS = 10000  # Default maximum characters allowed per prompt message


# ============================================================================
# Playwright Selectors
# ============================================================================

# Message container selectors - used to find chat response messages
MESSAGE_SELECTORS = (
    'div[role="article"]',
    "div.chat-response",
    'div[data-content="message"]',
    'div[aria-live="polite"]',
    'div[role="dialog"] article',
    '[data-testid="message"]',
)

# Raw markdown selectors - for extracting pre-formatted code blocks
RAW_MARKDOWN_SELECTORS = (
    'div[data-testid="markdown"] pre',
    'div:has(> pre)[data-testid="markdown"] pre',
    "div.rounded-b-xl pre",
    "pre.markdown",
)

# Authentication selectors
SIGN_IN_SELECTORS = (
    'role=link[name="Sign in"]',
    'role=button[name="Sign in"]',
    "text=Sign in",
    'a:has-text("Sign in")',
    'button:has-text("Sign in")',
)

LOGGED_IN_INDICATORS = (
    '[aria-label*="Account"]',
    '[data-testid*="user"]',
    '[data-testid*="profile"]',
    'button[aria-label*="profile" i]',
)

# File upload selectors
PLUS_BUTTON_SELECTOR = '[data-testid="plus-button"]'
FILE_UPLOAD_BUTTON_SELECTOR = '[data-testid="file-upload-button"]'

# Download selectors
DOWNLOAD_BUTTON_SELECTORS = (
    "a[download]",
    'button[aria-label="Download"]',
    'button[data-testid="download-button"]',
    'button:has-text("Download")',
)

# UI cleanup selectors
UI_CLEANUP_SELECTORS = (
    'button:has-text("Accept all")',
    'button:has-text("Accept")',
    'button:has-text("Got it")',
    'button:has-text("Continue")',
    'button:has-text("Allow")',
    'button:has-text("OK")',
    'button[aria-label="Close"]',
    'button:has-text("Not now")',
)

# ============================================================================
# Text Processing Patterns
# ============================================================================

# Citation pattern for removing Copilot citations from responses
CITATION_PATTERN = re.compile(r"\[_\{\{\{CITATION\{\{\{_?\d+\{\]\([^)]+\)")

# Status prefixes to filter out from chat messages
STATUS_PREFIXES = ("You said", "Uploading file", "Uploaded file", "Working on it")

# Noisy phrases to filter out from responses
NOISY_PHRASES = (
    "Nice to see you",
    "Copilot may make mistakes",
    "Your conversations are personalised",
    "Quick response",
    "Create an image",
    "Write a first draft",
    "Improve writing",
    "Design a logo",
    "Write a joke",
    "Rewrite a classic",
    "Draft an email",
    "Take a personality quiz",
    "Predict the future",
    "Improve communication",
)

# ============================================================================
# Markdown Instructions
# ============================================================================

MARKDOWN_INSTRUCTION = (
    "Respond strictly in raw, unrendered, well-structured Markdown which I can use in an .md file."
)

# ============================================================================
# File Upload Configuration
# ============================================================================

# Maximum file size for uploads (100 MB)
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024

# Allowed file extensions for upload
ALLOWED_FILE_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx",
    ".doc",
    ".docm",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".xlsb",
    ".csv",
    ".md",
    ".py",
    ".js",
    ".json",
    ".xml",
    ".html",
    ".css",
    ".pptx",
    ".ppt",
}

# ============================================================================
# Retry Configuration
# ============================================================================

MAX_RETRIES = 3
RETRY_DELAY_MS = 1000  # 1 second between retries
EXPONENTIAL_BACKOFF = True
