from pathlib import Path
import unittest

from mentohust_modern.config import default_client_exe
from mentohust_modern.ruijie import compute_v2_check, encode_byte, get_version_from_exe


class RuijieTests(unittest.TestCase):
    def test_encode_byte(self) -> None:
        self.assertEqual(encode_byte(0x13), 0x37)
        self.assertEqual(encode_byte(0x11), 0x77)

    def test_version_from_official_client(self) -> None:
        major, minor = get_version_from_exe(default_client_exe())
        self.assertEqual((major, minor), (5, 0))

    def test_v2_check_is_stable(self) -> None:
        seed = bytes.fromhex("0102030405060708090A0B0C0D0E0F10")
        value = compute_v2_check(seed, default_client_exe())
        self.assertEqual(value, "95404FBA517E4F6399F28A53F11CFBD7")


if __name__ == "__main__":
    unittest.main()
