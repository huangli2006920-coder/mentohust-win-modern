import unittest
from unittest.mock import Mock

from mentohust_modern.client import DISCONNECT, ECHO, MentohustClient
from mentohust_modern.config import MentohustConfig


class ClientStopTests(unittest.TestCase):
    def test_stop_sends_logoff_without_waiting_for_the_worker_thread(self) -> None:
        client = MentohustClient(MentohustConfig())
        client.socket = object()
        client.state = ECHO
        client._send_logoff = Mock()  # type: ignore[method-assign]

        client.stop(wait=False)

        client._send_logoff.assert_called_once()
        self.assertTrue(client.stop_event.is_set())
        self.assertEqual(client.state, DISCONNECT)


if __name__ == "__main__":
    unittest.main()
