from pathlib import Path
import unittest

from mentohust_modern.openwrt import load_openwrt_config_text


SAMPLE = """
config mentohust 'config'
        option enable '1'
        option username 'student'
        option password 'secret'
        option interface 'eth0'
        option ipaddr '0.0.0.0'
        option gateway '10.0.0.1'
        option mask '255.255.255.0'
        option ping 'www.baidu.com'
        option timeout '8'
        option interval '30'
        option wait '15'
        option fail_number '0'
        option multicast_address '1'
        option dhcp_mode '2'
        option dhcp_script 'udhcpc -i'
        option version '5.00'
        option dns '8.8.8.8'
"""


class OpenWrtConfigTests(unittest.TestCase):
    def test_parse_sample(self) -> None:
        config = load_openwrt_config_text(SAMPLE)
        self.assertTrue(config.enable)
        self.assertEqual(config.username, "student")
        self.assertEqual(config.password, "secret")
        self.assertEqual(config.interface_description, "eth0")
        self.assertEqual(config.gateway, "10.0.0.1")
        self.assertEqual(config.multicast_address, 1)
        self.assertEqual(config.dhcp_mode, 2)
        self.assertEqual(config.version, "5.00")


if __name__ == "__main__":
    unittest.main()

