"""
tests/test_config.py
===================
Unit tests verifying environment configuration, key security, and Gemini API connection.
All external connections are mocked to ensure tests run offline without network access or secrets.
"""

from unittest.mock import MagicMock, patch
from backend.config import (
    get_settings,
    mask_secret,
    sanitize_text,
    test_gemini_connection as check_gemini_connection,
)


def test_settings_properties():
    settings = get_settings()
    settings.reload()

    # Check key presence and model default
    assert settings.is_gemini_configured is True
    assert settings.gemini_api_key is not None
    assert len(settings.gemini_api_key) > 10
    assert settings.gemini_model in ("gemini-3.8-flash", "gemini-2.5-flash")


def test_secret_masking():
    settings = get_settings()
    raw_key = settings.gemini_api_key or "AIzaSyDxyzFakeKeyForTesting12345"
    masked = mask_secret(raw_key)

    # Must be masked
    assert raw_key != masked
    assert masked.startswith(raw_key[:4])
    assert masked.endswith(raw_key[-4:])
    assert "..." in masked

    # Ensure repr masks secrets
    repr_str = repr(settings)
    assert raw_key not in repr_str
    assert masked in repr_str


def test_sanitize_text():
    settings = get_settings()
    raw_key = settings.gemini_api_key or "AIzaSyDxyzFakeKeyForTesting12345"
    dirty_text = f"Error communicating with https://generativelanguage.googleapis.com?key={raw_key}"
    clean_text = sanitize_text(dirty_text, secrets=[raw_key])

    assert raw_key not in clean_text
    assert mask_secret(raw_key) in clean_text


def test_safe_gemini_connection_success():
    """Mocked test ensuring safe connection verification without hitting live API."""
    settings = get_settings()
    raw_key = settings.gemini_api_key

    mock_resp = MagicMock()
    mock_resp.text = "OK"

    with patch("google.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.models.generate_content.return_value = mock_resp
        mock_client_cls.return_value = mock_instance

        result = check_gemini_connection()

    assert result["success"] is True
    assert "model" in result
    # Crucial safety check: raw key must NEVER appear in the result dictionary
    result_str = str(result)
    if raw_key:
        assert raw_key not in result_str


def test_safe_gemini_connection_error_sanitization():
    """Ensure error messages are sanitized when connection fails."""
    settings = get_settings()
    raw_key = settings.gemini_api_key

    with patch("google.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        # Simulate error containing raw secret
        mock_instance.models.generate_content.side_effect = RuntimeError(f"Connection failed for key {raw_key}")
        mock_client_cls.return_value = mock_instance

        result = check_gemini_connection()

    assert result["success"] is False
    if raw_key:
        assert raw_key not in result["error"]
        assert mask_secret(raw_key) in result["error"]
