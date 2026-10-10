"""
backend/config.py
=================
Environment configuration loader for SpiritIQ.
Loads variables safely via python-dotenv and provides secure access
with secret masking so API keys are NEVER exposed in logs, exceptions, or string outputs.
Integrated with Groq API for high-speed LLM inference.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Automatically locate and load .env file from project root without overwriting existing environment
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=False)
else:
    load_dotenv(override=False)  # Fallback to system env or current directory


def mask_secret(value: Optional[str], visible_chars: int = 4) -> str:
    """
    Safely mask sensitive strings for display in logs or debug views.
    Example: 'gsk_1234567890' -> 'gsk_...7890' or '****' if too short.
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
    targets: list[str] = []
    if secrets:
        for s in secrets:
            if s and s.strip():
                targets.append(s.strip())
    # Always include current settings secrets as well
    try:
        curr_settings = get_settings()
        for s in [curr_settings.groq_api_key, curr_settings.google_maps_api_key]:
            if s and s.strip() and s.strip() not in targets:
                targets.append(s.strip())
    except Exception:
        pass

    for secret in targets:
        if secret in clean:
            clean = clean.replace(secret, mask_secret(secret))
    return clean


class Settings:
    """
    Centralized application settings with strict secrecy safeguards.
    """

    DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

    def __init__(self) -> None:
        self._groq_api_key: Optional[str] = None
        self._groq_model: str = self.DEFAULT_GROQ_MODEL
        self._google_maps_api_key: Optional[str] = None
        self.reload()

    def reload(self) -> None:
        """Reload configuration from current environment variables."""
        raw_groq = os.getenv("GROQ_API_KEY")
        self._groq_api_key = raw_groq.strip() if raw_groq and raw_groq.strip() else None

        raw_model = os.getenv("GROQ_MODEL")
        self._groq_model = raw_model.strip() if raw_model and raw_model.strip() else self.DEFAULT_GROQ_MODEL

        raw_maps = os.getenv("GOOGLE_MAPS_API_KEY")
        self._google_maps_api_key = raw_maps.strip() if raw_maps and raw_maps.strip() else None

    @property
    def groq_api_key(self) -> Optional[str]:
        """Groq API key for AI orchestration."""
        return self._groq_api_key

    @property
    def groq_model(self) -> str:
        """Groq model name (defaults to 'llama-3.3-70b-versatile')."""
        return self._groq_model or self.DEFAULT_GROQ_MODEL

    @property
    def google_maps_api_key(self) -> Optional[str]:
        """Google Maps API key for Places, Routes, and Geocoding."""
        return self._google_maps_api_key

    @property
    def is_groq_configured(self) -> bool:
        """Check whether Groq API key is configured."""
        return bool(self._groq_api_key and self._groq_api_key.strip())

    @property
    def is_google_maps_configured(self) -> bool:
        """Check whether Google Maps API key is configured."""
        return bool(self._google_maps_api_key and self._google_maps_api_key.strip())

    # Backward compatibility properties
    @property
    def gemini_api_key(self) -> Optional[str]:
        return self._groq_api_key

    @property
    def gemini_model(self) -> str:
        return self.groq_model

    @property
    def is_gemini_configured(self) -> bool:
        return self.is_groq_configured

    def validate_keys(self) -> Dict[str, bool]:
        """
        Check which external service keys are present without leaking their values.
        Returns a dictionary of service names mapped to boolean status.
        """
        return {
            "groq_api_key_set": self.is_groq_configured,
            "groq_model_set": bool(self.groq_model and self.groq_model.strip()),
            "google_maps_api_key_set": self.is_google_maps_configured,
            # Backward-compatible keys for existing UI components
            "gemini_api_key_set": self.is_groq_configured,
            "gemini_model_set": bool(self.groq_model and self.groq_model.strip()),
        }

    def __repr__(self) -> str:
        """Safe representation that guarantees API keys are NEVER printed."""
        return (
            f"<Settings "
            f"groq_api_key={mask_secret(self._groq_api_key)} "
            f"groq_model='{self.groq_model}' "
            f"google_maps_api_key={mask_secret(self._google_maps_api_key)}>"
        )

    def __str__(self) -> str:
        return self.__repr__()


# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    """Retrieve global settings instance."""
    return settings


def test_groq_connection() -> Dict[str, Any]:
    """
    Safely tests connectivity with Groq API using configured credentials.
    Guarantees no raw API keys are exposed in return values, logs, or exceptions.
    Do not claim Groq is connected until a real API request has succeeded.
    """
    s = get_settings()
    if not s.is_groq_configured:
        return {
            "success": False,
            "model": s.groq_model,
            "error": "GROQ_API_KEY is not configured or empty in .env",
        }

    try:
        from groq import Groq
        client = Groq(api_key=s.groq_api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Respond with only the single word: OK",
                }
            ],
            model=s.groq_model,
            max_tokens=10,
        )
        reply = (
            chat_completion.choices[0].message.content.strip()
            if chat_completion.choices and chat_completion.choices[0].message.content
            else "OK"
        )
        return {
            "success": True,
            "model": s.groq_model,
            "masked_key": mask_secret(s.groq_api_key),
            "message": f"Groq API connected successfully ({reply})",
        }
    except Exception as exc:
        safe_msg = sanitize_text(str(exc), secrets=[s.groq_api_key])
        return {
            "success": False,
            "model": s.groq_model,
            "masked_key": mask_secret(s.groq_api_key),
            "error": f"Groq API connection failed: {safe_msg}",
        }


# Compatibility alias
test_gemini_connection = test_groq_connection


def test_google_maps_status() -> Dict[str, Any]:
    """
    Safely checks Google Maps configuration status without making paid external network requests.
    Guarantees no raw API keys are exposed.
    """
    s = get_settings()
    s.reload()
    if not s.is_google_maps_configured:
        return {
            "configured": False,
            "masked_key": "<NOT_SET>",
            "status": "Google Maps API key not configured in .env (OpenStreetMap & OSRM active as free primary engine; calibrated Dijkstra corridor fallback active)",
            "fallback_ready": True,
            "open_providers_active": True,
        }
    return {
        "configured": True,
        "masked_key": mask_secret(s.google_maps_api_key),
        "status": "Google Maps API key configured in .env (Optional override; OpenStreetMap, OSRM & Dijkstra fallbacks ready)",
        "fallback_ready": True,
        "open_providers_active": True,
    }

