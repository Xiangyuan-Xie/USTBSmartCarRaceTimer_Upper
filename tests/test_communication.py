import unittest
from unittest.mock import MagicMock, patch

from communication_threads.communication import (
    SerialPortThread,
    TcpServerThread,
    UdpServerThread,
    WebSocketClientThread,
    parse_data,
)


class TestCommunication(unittest.TestCase):
    def test_parse_data(self):
        callback_mock = MagicMock()
        patterns = [(r"\{([-+]?\d*\.\d+|\d+)\}", callback_mock)]

        # Test valid data
        parse_data("{12345}", patterns)
        callback_mock.assert_called_with(12.345)

        # Test invalid data
        callback_mock.reset_mock()
        parse_data("invalid", patterns)
        callback_mock.assert_not_called()

    @patch("communication_threads.communication.serial.Serial")
    def test_serial_thread(self, mock_serial):
        # Setup mock
        mock_instance = MagicMock()
        mock_serial.return_value = mock_instance
        mock_instance.in_waiting = 1
        mock_instance.readline.return_value = b"{12345}\n"

        # Init thread
        thread = SerialPortThread("COM1", 9600)

        # Update callbacks to use mocked signal
        thread.real_received = MagicMock()
        thread.patterns_callbacks = [
            (r"\{([-+]?\d*\.\d+|\d+)\}", thread.real_received.emit),
        ]

        # Simulate logic
        data = mock_instance.readline().decode("ascii").strip()
        parse_data(data, thread.patterns_callbacks)

        thread.real_received.emit.assert_called_with(12.345)

        thread.stop()
        self.assertFalse(thread.running)

    @patch("communication_threads.communication.socket.socket")
    def test_tcp_server_thread(self, mock_socket_cls):
        mock_socket = MagicMock()
        mock_socket_cls.return_value.__enter__.return_value = mock_socket

        thread = TcpServerThread(port=12345)

        # Mock signal and update callbacks
        thread.real_received = MagicMock()
        thread.patterns_callbacks = [
            (r"\{([-+]?\d*\.\d+|\d+)\}", thread.real_received.emit),
        ]

        # Verify init
        self.assertEqual(thread.port, 12345)

        # Simulate receiving data logic manually since we can't easily run the loop
        data_str = "{67890}"
        parse_data(data_str, thread.patterns_callbacks)

        thread.real_received.emit.assert_called_with(67.890)

        thread.stop()
        self.assertFalse(thread.running)

    @patch("communication_threads.communication.socket.socket")
    def test_udp_server_thread(self, mock_socket_cls):
        mock_socket = MagicMock()
        mock_socket_cls.return_value.__enter__.return_value = mock_socket

        thread = UdpServerThread(port=54321)

        # Mock signal and update callbacks
        thread.real_received = MagicMock()
        thread.patterns_callbacks = [
            (r"\{([-+]?\d*\.\d+|\d+)\}", thread.real_received.emit),
        ]

        # Verify init
        self.assertEqual(thread.port, 54321)

        # Simulate receiving data logic
        data_str = "{11122}"
        parse_data(data_str, thread.patterns_callbacks)

        thread.real_received.emit.assert_called_with(11.122)

        thread.stop()
        self.assertFalse(thread.running)

    @patch("communication_threads.communication.websockets.connect")
    @patch("communication_threads.communication.asyncio")
    def test_websocket_client(self, mock_asyncio, mock_connect):
        thread = WebSocketClientThread("ws://test:8000")

        thread.real_received = MagicMock()
        thread.patterns_callbacks = [
            (r"\{([-+]?\d*\.\d+|\d+)\}", thread.real_received.emit),
        ]

        parse_data("{5000}", thread.patterns_callbacks)
        thread.real_received.emit.assert_called_with(5.0)

        thread.stop()
        self.assertFalse(thread.running)
