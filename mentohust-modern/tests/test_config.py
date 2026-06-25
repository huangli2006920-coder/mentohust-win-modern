from pathlib import Path
import tempfile
import unittest

from mentohust_modern.config import MentohustConfig


class ConfigTests(unittest.TestCase):
    def test_auto_connect_roundtrip(self) -> None:
        config = MentohustConfig(auto_connect=True, username="user")
        loaded = MentohustConfig.from_dict(config.to_dict())
        self.assertTrue(loaded.auto_connect)
        self.assertEqual(loaded.username, "user")

    def test_save_and_load_json(self) -> None:
        config = MentohustConfig(auto_connect=True, username="user", password="secret")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            config.save_json(path)
            loaded = MentohustConfig.load_json(path)
        self.assertTrue(loaded.auto_connect)
        self.assertEqual(loaded.password, "secret")


if __name__ == "__main__":
    unittest.main()
