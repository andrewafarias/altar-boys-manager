import sys
import os
from unittest.mock import patch, MagicMock
from src.acolito_manager.utils import open_file

def test_open_file_windows():
    with patch("sys.platform", "win32"):
        with patch("os.startfile", create=True) as mock_startfile:
            open_file("test_path.pdf")
            mock_startfile.assert_called_once_with("test_path.pdf")

def test_open_file_mac():
    with patch("sys.platform", "darwin"):
        with patch("subprocess.call") as mock_call:
            open_file("test_path.pdf")
            mock_call.assert_called_once_with(["open", "test_path.pdf"])

def test_open_file_linux():
    with patch("sys.platform", "linux"):
        with patch("subprocess.call") as mock_call:
            open_file("test_path.pdf")
            mock_call.assert_called_once_with(["xdg-open", "test_path.pdf"])

def test_open_file_exception_handling():
    with patch("sys.platform", "win32"):
        with patch("os.startfile", create=True, side_effect=Exception("Error")):
            # Should not raise exception
            open_file("test_path.pdf")
