"""
backend/config.py
=================
Environment configuration loader for SpiritIQ.
Loads variables safely via python-dotenv and provides secure access
with secret masking so API keys are NEVER exposed in logs, exceptions, or string outputs.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Automatically locate and load .env file from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    load_dotenv()  # Fallback to system env or current directory


def mask_secret(value: Optional[str], visible_chars: int = 4) -> str:
    """
    Safely mask sensitive strings for display in logs or debug views.
    Example: 'AIzaSyDxyz123' -> 'AIza...3' or '****' if too short.
    """
    if not value:
        return "<NOT_SET>"
    val = value.strip()
    if len(val) <= visible_chars * 2:
        return "*" * len(val)
    return f"{val[:visible_chars]}...{val[-visible_chars:]}"


def sanitize_text(text: str, secrets: Optional[list[Optional[str]]] = None) -> str:
    """
    Scrub all occurrences of secret values from an error message, stack trace, or log.
    """
    if not text:
        return text
    clean = str(text)
    targets = secrets or [settings.gemini_api_key, settings.google_maps_api_key]
    for secret in targets:
        if secret and secret.strip() and secret.strip() in clean:
            clean = clean.replace(secret.strip(), mask_secret(secret.strip()))
    return clean


class Settings:
    """
    Centralized application settings with strict secrecy safeguards.
    """

    def __init__(self) -> None:
        self._gemini_api_key: Optional[str] = None
        self._gemini_model: str = "gemini-3.8-flash"
        self._google_maps_api_key: Optional[str] = None
        self.reload()

    def reload(self) -> None:
        """Reload configuration from .env file and environment."""
        if ENV_PATH.exists():
            load_dotenv(dotenv_path=ENV_PATH, override=True)
        self._gemini_api_key = os.getenv("GEMINI_API_KEY")
        self._gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self._google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    @property
    def gemini_api_key(self) -> Optional[str]:
        """Google Gemini API key for AI orchestration."""
        return self._gemini_api_key

    @property
    def gemini_model(self) -> str:
        """Google Gemini model name (defaults to 'gemini-3.8-flash')."""
        return self._gemini_model or "gemini-3.8-flash"

    @property
    def google_maps_api_key(self) -> Optional[str]:
        """Google Maps API key for Places, Routes, and Geocoding."""
        return self._google_maps_api_key

    @property
    def is_gemini_configured(self) -> bool:
        """Check whether Gemini API key is configured."""
        return bool(self._gemini_api_key and self._gemini_api_key.strip())

    @property
    def is_google_maps_configured(self) -> bool:
        """Check whether Google Maps API key is configured."""
        return bool(self._google_maps_api_key and self._google_maps_api_key.strip())

    def validate_keys(self) -> Dict[str, bool]:
        """
        Check which external service keys are present without leaking their values.
        Returns a dictionary of service names mapped to boolean status.
        """
        return {
            "gemini_api_key_set": self.is_gemini_configured,
            "gemini_model_set": bool(self.gemini_model and self.gemini_model.strip()),
            "google_maps_api_key_set": self.is_google_maps_configured,
        }

    def __repr__(self) -> str:
        """Safe representation that guarantees API keys are NEVER printed."""
        return (
            f"<Settings "
            f"gemini_api_key={mask_secret(self._gemini_api_key)} "
            f"gemini_model='{self.gemini_model}' "
            f"google_maps_api_key={mask_secret(self._google_maps_api_key)}>"
        )

    def __str__(self) -> str:
        return self.__repr__()


# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    """Retrieve global settings instance."""
    return settings


def test_gemini_connection() -> Dict[str, Any]:
    """
    Safely tests connectivity with Google Gemini API using configured credentials.
    Guarantees no raw API keys are exposed in return values, logs, or exceptions.
    """
    s = get_settings()
    if not s.is_gemini_configured:
        return {
            "success": False,
            "model": s.gemini_model,
            "error": "GEMINI_API_KEY is not configured or empty in .env",
        }

    try:
        from google import genai
        client = genai.Client(api_key=s.gemini_api_key)
        response = client.models.generate_content(
            model=s.gemini_model,
            contents="Respond with only the single word: OK",
        )
        reply = response.text.strip() if response and response.text else "OK"
        return {
            "success": True,
            "model": s.gemini_model,
            "masked_key": mask_secret(s.gemini_api_key),
            "message": f"Gemini API connected successfully ({reply})",
        }
    except Exception as exc:
        safe_msg = sanitize_text(str(exc), secrets=[s.gemini_api_key])
        return {
            "success": False,
            "model": s.gemini_model,
            "masked_key": mask_secret(s.gemini_api_key),
            "error": f"Gemini API connection failed: {safe_msg}",
        }
