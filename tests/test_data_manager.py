import sys
import os
from pathlib import Path

# Add src to sys.path to allow importing acolito_manager
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from acolito_manager.data_manager import default_birthday_settings

def test_default_birthday_settings_keys_and_values():
    """Test that the default birthday settings have the expected keys and values."""
    settings = default_birthday_settings()

    expected_settings = {
        "enabled": False,
        "whatsapp_group": "",
        "message_template": "Feliz aniversário, {nome}! 🎂🎉",
        "send_time": "08:00",
        "muted_birthdate_notifications": [],
    }

    assert settings == expected_settings

def test_default_birthday_settings_is_new_instance():
    """Test that calling default_birthday_settings returns a new dictionary instance each time."""
    settings_1 = default_birthday_settings()
    settings_2 = default_birthday_settings()

    assert settings_1 is not settings_2
    assert settings_1["muted_birthdate_notifications"] is not settings_2["muted_birthdate_notifications"]

    # Mutating one shouldn't affect the other
    settings_1["enabled"] = True
    settings_1["muted_birthdate_notifications"].append("User1")

    assert settings_2["enabled"] is False
    assert len(settings_2["muted_birthdate_notifications"]) == 0
