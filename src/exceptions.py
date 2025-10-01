"""Custom exceptions for the MS365 Copilot Automation toolkit.

This module defines a hierarchy of exceptions that provide clear, specific
error messages and make error handling more precise throughout the application.
"""


class CopilotError(Exception):
    """Base exception for all Copilot automation errors.

    All custom exceptions in this package inherit from this base class,
    making it easy to catch all automation-related errors.
    """


class AuthenticationError(CopilotError):
    """Raised when authentication to MS365 fails."""


class FileOperationError(CopilotError):
    """Base exception for file-related operations.

    This includes uploads, downloads, and file validation errors.
    """


class FileUploadError(FileOperationError):
    """Raised when a file upload to Copilot fails.

    This can occur due to:
    - Network issues
    - File size limits
    - Unsupported file types
    - UI interaction failures
    """


class FileValidationError(FileOperationError):
    """Raised when a file fails validation before upload.

    This includes:
    - File doesn't exist
    - File is too large
    - File type not allowed
    - File is not readable
    """


class DownloadError(FileOperationError):
    """Raised when downloading an artifact from Copilot fails.

    This can occur when:
    - No download is available
    - Download times out
    - Network issues occur
    - Save location is invalid
    """


class DownloadTimeoutError(DownloadError):
    """Raised when waiting for a download times out.

    This is a specific type of download error indicating that
    Copilot did not provide a downloadable artifact within the
    expected timeframe.
    """


class ChatError(CopilotError):
    """Base exception for chat-related operations."""


class UIInteractionError(CopilotError):
    """Raised when UI interactions fail.

    This includes:
    - Elements not found
    - Elements not visible
    - Click failures
    - Navigation issues
    """


class SelectorNotFoundError(UIInteractionError):
    """Raised when a Playwright selector cannot find an element."""


class ConfigurationError(CopilotError):
    """Raised when there are configuration or setup issues."""


class BrowserError(CopilotError):
    """Raised when browser operations fail."""


def format_error_context(error: Exception, context: dict | None = None) -> str:
    """Format an error message with additional context."""
    base_msg = str(error)
    if not context:
        return base_msg

    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    return f"{base_msg} (Context: {context_str})"
