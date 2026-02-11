import re
import socket
import asyncio
import websockets
import serial
from PySide6.QtCore import QThread, Signal


def parse_data(data, pattern_callbacks):
    """
    通用函数，用于匹配指定模式并触发相应的回调。

    :param data: str，要解析的字符串。
    :param pattern_callbacks: list，包含元组，每个元组定义一个模式和回调函数。
                              格式为 [(pattern, callback), ...]。
    """
    for pattern, callback in pattern_callbacks:
        match = re.search(pattern, data)
        if match:
            message = float(match.group(1)) / 1000
            callback(message)

class WebSocketClientThread(QThread):
    real_received = Signal(float)
    final_received = Signal(float)
    timer_reset = Signal()
    send_status = Signal(str)
    message_received = Signal(str)

    def __init__(self, uri="ws://117.72.54.78:4001"):
        super().__init__()
        self.uri = uri
        self.running = True
        self.loop = None
        self.websocket = None
        self.patterns_callbacks = [
            (r"\{([-+]?\d*\.\d+|\d+)\}", self.real_received.emit),
            (r"\[([-+]?\d*\.\d+|\d+)\]", self.final_received.emit),
        ]

    def run(self):
        # 新建一个事件循环，避免阻塞主线程
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.websocket_loop())

    async def websocket_loop(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            async with self.websocket:
                print(f"已连接到 {self.uri}")
                while self.running:
                    try:
                        data = await self.websocket.recv()
                        data = data.strip()
                        self.message_received.emit(data)
                        print(f"[WS] {data}")

                        if "Reset" in data:
                            self.timer_reset.emit()
                        else:
                            try:
                                parse_data(data, self.patterns_callbacks)
                            except Exception:
                                continue

                    except websockets.ConnectionClosed:
                        print("服务器连接关闭")
                        break
                    except Exception as e:
                        print(f"WebSocket错误: {e}")
                        await asyncio.sleep(1)
        except Exception as e:
            print(f"无法连接到服务器: {e}")

    def stop(self):
        self.running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
    def send_message(self, message: str):
        """发送消息，如果未连接则忽略"""
        if self.websocket and self.loop and self.loop.is_running():
            # 确保在事件循环线程安全调用
            asyncio.run_coroutine_threadsafe(self.websocket.send(message), self.loop)
        else:
            print("WebSocket未连接，消息未发送")

class SerialPortThread(QThread):
    real_received = Signal(float)
    final_received = Signal(float)
    timer_reset = Signal()
    send_status = Signal(str)
    message_received = Signal(str)

    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.patterns_callbacks = [
            (r"\{([-+]?\d*\.\d+|\d+)\}", self.real_received.emit),
            (r"\[([-+]?\d*\.\d+|\d+)\]", self.final_received.emit),
        ]

        try:
            self.serial_connection = serial.Serial(
                self.port, self.baudrate, bytesize=8, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, timeout=1
            )
            self.running = True
        except Exception as e:
            self.send_status.emit(f"打开串口失败：{e}")
            self.running = False
            return

        self.send_status.emit(f"串口打开成功！（绑定端口：{self.port}, 波特率：{self.baudrate}）")

    def run(self):
        try:
            while self.running:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.readline().decode("ascii", errors="ignore").strip()
                    print(f"[Serial from {self.port}] {data}")
                    self.message_received.emit(data)
                    if "Reset" in data:
                        self.timer_reset.emit()
                    else:
                        try:
                            parse_data(data, self.patterns_callbacks)
                        except Exception:
                            continue
        except Exception as e:
            self.stop()
            self.send_status.emit(f"串口连接崩溃: {e}")

    def stop(self):
        self.running = False
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()


class TcpServerThread(QThread):
    real_received = Signal(float)
    final_received = Signal(float)
    timer_reset = Signal()
    send_status = Signal(str)

    def __init__(self, host="0.0.0.0", port=32767):
        super().__init__()
        self.host = host
        self.port = port
        self.running = True
        self.clients = []
        self.patterns_callbacks = [
            (r"\{([-+]?\d*\.\d+|\d+)\}", self.real_received.emit),
            (r"\[([-+]?\d*\.\d+|\d+)\]", self.final_received.emit),
        ]

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_server:
            tcp_server.bind((self.host, self.port))
            tcp_server.listen(5)
            tcp_server.settimeout(1.0)

            while self.running:
                try:
                    client_socket, client_address = tcp_server.accept()
                except socket.timeout:
                    continue
                else:
                    with client_socket:
                        self.clients.append(client_socket)
                        while self.running:
                            try:
                                data = client_socket.recv(1024)
                                if not data:
                                    break
                                data = data.decode("ascii", errors="ignore").strip()

                                if "Reset" in data:
                                    self.timer_reset.emit()
                                else:
                                    try:
                                        parse_data(data, self.patterns_callbacks)
                                    except Exception:
                                        continue
                            except ConnectionResetError:
                                break

                        self.clients.remove(client_socket)

    def stop(self):
        self.running = False


class UdpServerThread(QThread):
    real_received = Signal(float)
    final_received = Signal(float)
    timer_reset = Signal()
    send_status = Signal(str)

    def __init__(self, host="0.0.0.0", port=32767):
        super().__init__()
        self.host = host
        self.port = port
        self.running = True
        self.patterns_callbacks = [
            (r"\{([-+]?\d*\.\d+|\d+)\}", self.real_received.emit),
            (r"\[([-+]?\d*\.\d+|\d+)\]", self.final_received.emit),
        ]

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_server:
            udp_server.bind((self.host, self.port))

            while True:
                try:
                    data, addr = udp_server.recvfrom(1024)
                except socket.timeout:
                    continue
                except OSError:
                    break  # 套接字被关闭
                try:
                    data_str = data.decode('utf-8', errors='ignore').strip()
                except Exception as e:
                    print(f"解码错误: {e}")
                    continue

                # 打印收到的数据
                print(f"[UDP from {addr}] {data_str}")

                # 处理数据
                if "Reset" in data_str:
                    self.timer_reset.emit()
                else:
                    try:
                        parse_data(data_str, self.patterns_callbacks)
                    except Exception:
                        continue

    def stop(self):
        self.running = False
