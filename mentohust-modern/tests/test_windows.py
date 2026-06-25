import os
import unittest

from mentohust_modern.windows import get_system_ui_font, hidden_subprocess_kwargs


class WindowsHelperTests(unittest.TestCase):
    def test_hidden_subprocess_kwargs_have_expected_keys(self) -> None:
        kwargs = hidden_subprocess_kwargs()
        if os.name == "nt":
            self.assertIn("startupinfo", kwargs)
            self.assertIn("creationflags", kwargs)
        else:
            self.assertEqual(kwargs, {})

    def test_get_system_ui_font_returns_name_and_size(self) -> None:
        family, size = get_system_ui_font()
        self.assertTrue(family)
        self.assertGreaterEqual(size, 9)


if __name__ == "__main__":
    unittest.main()
