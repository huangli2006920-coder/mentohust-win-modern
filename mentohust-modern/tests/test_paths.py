import unittest

from mentohust_modern.app_paths import default_log_path, default_profile_path


class PathTests(unittest.TestCase):
    def test_default_paths_have_expected_filenames(self) -> None:
        self.assertEqual(default_profile_path().name, "default.json")
        self.assertEqual(default_log_path().name, "mentohust-win-modern.log")


if __name__ == "__main__":
    unittest.main()
