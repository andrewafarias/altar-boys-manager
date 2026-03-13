import sys
import os
from pathlib import Path

# Add src to sys.path to allow importing acolito_manager
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from acolito_manager.utils import detect_weekday, names_list_to_text

def test_detect_weekday_full_date():
    assert detect_weekday("23/10/2023") == "Segunda-feira"
    assert detect_weekday("24/10/2023") == "Terça-feira"
    assert detect_weekday("25/10/2023") == "Quarta-feira"
    assert detect_weekday("26/10/2023") == "Quinta-feira"
    assert detect_weekday("27/10/2023") == "Sexta-feira"
    assert detect_weekday("28/10/2023") == "Sábado"
    assert detect_weekday("29/10/2023") == "Domingo"

def test_detect_weekday_with_spaces():
    assert detect_weekday(" 23/10/2023 ") == "Segunda-feira"

from unittest.mock import patch
from datetime import datetime

def test_detect_weekday_no_year():
    # Mock datetime.now() to return a fixed date, e.g., in 2024 (leap year)
    with patch("acolito_manager.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 1, 1)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        # 01/01/2024 was a Monday (Segunda-feira)
        assert detect_weekday("01/01") == "Segunda-feira"
        # 29/02/2024 was a Thursday (Quinta-feira)
        assert detect_weekday("29/02") == "Quinta-feira"

    # Mock datetime.now() to return a date in 2023 (non-leap year)
    with patch("acolito_manager.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2023, 1, 1)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        # 01/01/2023 was a Sunday (Domingo)
        assert detect_weekday("01/01") == "Domingo"

def test_detect_weekday_invalid_dates():
    # Invalid day/month
    assert detect_weekday("32/01/2023") == ""
    assert detect_weekday("01/13/2023") == ""
    # Invalid Feb 29th
    assert detect_weekday("29/02/2023") == ""
    # Not enough parts
    assert detect_weekday("23/10") != "" # This should be valid as DD/MM
    assert detect_weekday("23") == ""
    # Non-numeric parts
    assert detect_weekday("abc/def/ghi") == ""
    assert detect_weekday("23/oct/2023") == ""

def test_detect_weekday_edge_cases():
    assert detect_weekday("") == ""
    assert detect_weekday("   ") == ""
    assert detect_weekday("/") == ""
    assert detect_weekday("//") == ""

def test_names_list_to_text():
    # Empty list
    assert names_list_to_text([]) == ""

    # One name
    assert names_list_to_text(["João"]) == "João"

    # Two names
    assert names_list_to_text(["João", "Maria"]) == "João e Maria"

    # Three names
    assert names_list_to_text(["João", "Maria", "José"]) == "João, Maria e José"

    # More than three names
    assert names_list_to_text(["João", "Maria", "José", "Ana", "Pedro"]) == "João, Maria, José, Ana e Pedro"
