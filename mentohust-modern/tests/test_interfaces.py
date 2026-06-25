from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from mentohust_modern.interfaces import has_active_wifi_connection


class InterfaceTests(unittest.TestCase):
    def test_has_active_wifi_connection_returns_true_on_true_stdout(self) -> None:
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="True\r\n", stderr="")
        with patch("mentohust_modern.interfaces.subprocess.run", return_value=completed):
            self.assertTrue(has_active_wifi_connection())

    def test_has_active_wifi_connection_returns_false_on_failure(self) -> None:
        completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="error")
        with patch("mentohust_modern.interfaces.subprocess.run", return_value=completed):
            self.assertFalse(has_active_wifi_connection())


if __name__ == "__main__":
    unittest.main()
