import unittest

from mentohust_modern.elevation import build_relaunch_parameters


class ElevationTests(unittest.TestCase):
    def test_build_relaunch_parameters_keeps_module_entrypoint(self) -> None:
        value = build_relaunch_parameters(["--demo", "hello world"], frozen=False)
        self.assertIn("-m mentohust_modern", value)
        self.assertIn("--demo", value)
        self.assertIn('"hello world"', value)

    def test_build_relaunch_parameters_for_frozen_app_omits_module_flag(self) -> None:
        value = build_relaunch_parameters(["--demo", "hello world"], frozen=True)
        self.assertNotIn("-m mentohust_modern", value)
        self.assertIn("--demo", value)
        self.assertIn('"hello world"', value)


if __name__ == "__main__":
    unittest.main()
