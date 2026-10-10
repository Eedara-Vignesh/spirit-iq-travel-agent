"""
tests/test_config.py
===================
Unit tests verifying environment configuration, key security, and Groq API connection.
All external connections are mocked to ensure tests run offline without network access or secrets.
"""

from unittest.mock import MagicMock, patch
import os

from backend.config import (
    Settings,
    get_settings,
    mask_secret,
    sanitize_text,
    test_groq_connection as check_groq_connection,
    test_gemini_connection as check_gemini_connection,
)


def test_settings_properties_and_defaults():
    settings = get_settings()

    # Model default must be configurable and non-empty
    assert settings.groq_model is not None
    assert len(settings.groq_model) > 0
    assert any(m in settings.groq_model.lower() for m in ["llama", "groq", "qwen"])

    # Key status validation
    status = settings.validate_keys()
    assert "groq_api_key_set" in status
    assert "groq_model_set" in status
    assert status["groq_model_set"] is True


def test_secret_masking():
    raw_key = "gsk_SampleTestGroqKeySecret123456789"
    masked = mask_secret(raw_key)

    # Must be masked
    assert raw_key != masked
    assert masked.startswith(raw_key[:4])
    assert masked.endswith(raw_key[-4:])
    assert "..." in masked

    # Test short secret masking
    short_key = "1234"
    assert mask_secret(short_key) == "****"
    assert mask_secret(None) == "<NOT_SET>"
    assert mask_secret("") == "<NOT_SET>"

    # Ensure repr never exposes raw secret
    with patch.dict(os.environ, {"GROQ_API_KEY": raw_key}):
        s = Settings()
        repr_str = repr(s)
        assert raw_key not in repr_str
        assert masked in repr_str


def test_sanitize_text():
    raw_key = "gsk_RealSecretThatShouldNeverBeLeaked"
    dirty_text = f"Error communicating with https://api.groq.com/openai/v1?auth={raw_key}"
    clean_text = sanitize_text(dirty_text, secrets=[raw_key])

    assert raw_key not in clean_text
    assert mask_secret(raw_key) in clean_text


def test_safe_groq_connection_success():
    """Mocked test ensuring safe connection verification without hitting live API."""
    mock_choice = MagicMock()
    mock_choice.message.content = "OK"
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_MockTestValidKey12345678"}), \
         patch("groq.Groq") as mock_groq_cls:
        settings = get_settings()
        settings.reload()

        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_completion
        mock_groq_cls.return_value = mock_instance

        result = check_groq_connection()

    assert result["success"] is True
    assert "model" in result
    assert "Groq API connected successfully" in result["message"]
    # Crucial safety check: raw key must NEVER appear in the result dictionary
    assert "gsk_MockTestValidKey12345678" not in str(result)
    assert result.get("masked_key") is not None


def test_safe_groq_connection_missing_key():
    """Verify safe handling when GROQ_API_KEY is not configured."""
    with patch.dict(os.environ, {"GROQ_API_KEY": ""}):
        settings = get_settings()
        settings.reload()

        result = check_groq_connection()

    assert result["success"] is False
    assert "GROQ_API_KEY is not configured" in result["error"]


def test_safe_groq_connection_error_sanitization():
    """Ensure error messages are sanitized when connection fails."""
    fake_key = "gsk_SecretLeakingInError123456"

    with patch.dict(os.environ, {"GROQ_API_KEY": fake_key}), \
         patch("groq.Groq") as mock_groq_cls:
        settings = get_settings()
        settings.reload()

        mock_instance = MagicMock()
        mock_instance.chat.completions.create.side_effect = RuntimeError(f"401 Unauthorized with token: {fake_key}")
        mock_groq_cls.return_value = mock_instance

        result = check_groq_connection()

    assert result["success"] is False
    assert fake_key not in result["error"]
    assert mask_secret(fake_key) in result["error"]


def test_backward_compatibility_alias():
    """Verify check_gemini_connection alias points to check_groq_connection."""
    assert check_gemini_connection is check_groq_connection


def test_google_maps_key_not_configured_fallback():
    """Verify safe handling and clear status when GOOGLE_MAPS_API_KEY is not configured."""
    from backend.config import test_google_maps_status
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": ""}):
        s = Settings()
        assert s.is_google_maps_configured is False
        assert s.validate_keys()["google_maps_api_key_set"] is False
        status_info = test_google_maps_status()
        assert status_info["configured"] is False
        assert status_info["fallback_ready"] is True
        assert "Dijkstra" in status_info["status"]


def test_google_maps_key_configured_and_masked():
    """Verify Google Maps key is properly detected, masked, and never exposed in representations."""
    from backend.config import test_google_maps_status
    fake_maps_key = "AIzaSyDummyMapsApiKeyForTesting12345678"
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": fake_maps_key}):
        s = Settings()
        assert s.is_google_maps_configured is True
        assert s.validate_keys()["google_maps_api_key_set"] is True
        assert fake_maps_key not in repr(s)
        assert mask_secret(fake_maps_key) in repr(s)

        # Sanitization check
        dirty_log = f"Google Maps request failed with key={fake_maps_key}"
        clean_log = sanitize_text(dirty_log, secrets=[fake_maps_key])
        assert fake_maps_key not in clean_log
        assert mask_secret(fake_maps_key) in clean_log

        # Safe status test
        status_info = test_google_maps_status()
        assert status_info["configured"] is True
        assert status_info["fallback_ready"] is True
        assert fake_maps_key not in str(status_info)
        assert status_info["masked_key"] == mask_secret(fake_maps_key)

