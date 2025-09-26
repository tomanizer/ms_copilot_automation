import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import keyring
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .logger import get_logger


load_dotenv(dotenv_path=Path(".env"), override=False)
_logger = get_logger(__name__)


class Settings(BaseModel):
    """Application settings loaded from env and keyring.

    Secrets precedence: environment variables first, then keyring (for
    sensitive keys), otherwise remain ``None``.
    """

    # Auth
    username: Optional[str] = Field(default=None, alias="M365_USERNAME")
    password: Optional[str] = Field(default=None, alias="M365_PASSWORD")
    mfa_secret: Optional[str] = Field(default=None, alias="M365_OTP_SECRET")
    copilot_url: str = Field(default="https://copilot.microsoft.com", alias="M365_COPILOT_URL")

    # Runtime
    output_directory: Path = Field(default=Path(os.getenv("OUTPUT_DIRECTORY", "./output")))
    browser_headless: bool = Field(default=(os.getenv("BROWSER_HEADLESS", "true").lower() == "true"))

    # Storage state
    storage_state_path: Path = Field(default=Path("playwright/auth/user.json"))

    class Config:
        populate_by_name = True

    def hydrate_from_keyring(self) -> None:
        """Fill missing sensitive values from OS keyring."""
        if not self.password:
            try:
                self.password = keyring.get_password("ms-copilot-automation", "M365_PASSWORD")
            except Exception as exc:
                _logger.debug("Keyring lookup for password failed: %s", exc)
        if not self.mfa_secret:
            try:
                self.mfa_secret = keyring.get_password("ms-copilot-automation", "M365_OTP_SECRET")
            except Exception as exc:
                _logger.debug("Keyring lookup for mfa_secret failed: %s", exc)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance with keyring hydration."""
    settings = Settings()
    settings.hydrate_from_keyring()
    settings.output_directory.mkdir(parents=True, exist_ok=True)
    settings.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
