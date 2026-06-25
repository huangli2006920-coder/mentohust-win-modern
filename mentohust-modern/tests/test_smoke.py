import unittest


class SmokeTests(unittest.TestCase):
    def test_import_gui_module(self) -> None:
        import mentohust_modern.gui  # noqa: F401

    def test_import_client_module(self) -> None:
        import mentohust_modern.client  # noqa: F401


if __name__ == "__main__":
    unittest.main()
