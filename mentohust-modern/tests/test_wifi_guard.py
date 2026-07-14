import unittest
from unittest.mock import patch

from mentohust_modern.interfaces import has_active_wifi_connection


class WifiGuardTests(unittest.TestCase):
    def test_missing_powershell_is_treated_as_no_wifi_connection(self) -> None:
        with patch("mentohust_modern.interfaces.subprocess.run", side_effect=OSError):
            self.assertFalse(has_active_wifi_connection())


if __name__ == "__main__":
    unittest.main()
