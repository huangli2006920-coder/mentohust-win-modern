import ctypes
import os
import threading
import unittest

from mentohust_modern.windows import (
    WM_ENDSESSION,
    WM_QUERYENDSESSION,
    SessionEndNotifier,
    get_system_ui_font,
    hidden_subprocess_kwargs,
)


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

    @unittest.skipUnless(os.name == "nt", "Windows only")
    def test_session_end_notifier_starts_and_stops(self) -> None:
        notifier = SessionEndNotifier(is_connected=lambda: False, on_session_end=lambda: None)
        self.assertTrue(notifier.start())
        notifier.stop()

    @unittest.skipUnless(os.name == "nt", "Windows only")
    def test_session_end_notifier_runs_cleanup_on_end_session(self) -> None:
        finished = threading.Event()
        notifier = SessionEndNotifier(is_connected=lambda: True, on_session_end=finished.set)
        self.assertTrue(notifier.start())
        try:
            ctypes.windll.user32.SendMessageW(notifier._hwnd, WM_QUERYENDSESSION, 0, 0)
            ctypes.windll.user32.SendMessageW(notifier._hwnd, WM_ENDSESSION, 1, 0)
            self.assertTrue(finished.wait(timeout=1))
        finally:
            notifier.stop()


if __name__ == "__main__":
    unittest.main()
