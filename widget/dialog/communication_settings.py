"""通信设置对话窗口"""

import datetime
import socket

import psutil
import serial.tools.list_ports
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QGridLayout, QMessageBox, QScrollArea, QTabWidget, QTextEdit, QVBoxLayout, QWidget

from widget.common import create_button, create_combo_box, create_label, create_line_edit
from widget.dialog.base import BaseDialog
from widget.round_indicator import RoundIndicator


class CommunicationSettingDialog(BaseDialog):
    serial_port_state_changed = Signal(tuple)
    tcp_server_state_changed = Signal(tuple)
    udp_server_state_changed = Signal(tuple)
    websocket_client_state_changed = Signal(tuple)
    send_status = Signal(str)

    def __init__(self, configuration, communication_thread):
        super().__init__()
        self.setWindowTitle("通信设置")
        self.configuration = configuration
        self.communication_thread = communication_thread

        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        # 通信设置
        communication_setting = QWidget()
        communication_setting_layout = QGridLayout(communication_setting)
        communication_setting_layout.setVerticalSpacing(10)  # 设置行间距为 10 像素

        # 串口通信状态（通信设置页）
        serial_connect_state = create_label("串口通信状态:")
        communication_setting_layout.addWidget(serial_connect_state, 0, 0)
        self.serial_connect_state_display = RoundIndicator()
        communication_setting_layout.addWidget(self.serial_connect_state_display, 0, 1)

        # TCP服务器状态（通信设置页）
        tcp_server_state = create_label("TCP服务器状态:")
        communication_setting_layout.addWidget(tcp_server_state, 1, 0)
        self.tcp_server_state_display = RoundIndicator()
        communication_setting_layout.addWidget(self.tcp_server_state_display, 1, 1)

        # UDP服务器状态（通信设置页）
        udp_server_state = create_label("UDP服务器状态:")
        communication_setting_layout.addWidget(udp_server_state, 2, 0)
        self.udp_server_state_display = RoundIndicator()
        communication_setting_layout.addWidget(self.udp_server_state_display, 2, 1)

        # WebSocket客户端状态（通信设置页）
        websocket_client_state = create_label("WebSocket状态:")
        communication_setting_layout.addWidget(websocket_client_state, 3, 0)
        self.websocket_client_state_display = RoundIndicator()
        communication_setting_layout.addWidget(self.websocket_client_state_display, 3, 1)

        # 选择端口（通信设置页）
        port = create_label("串口:")
        communication_setting_layout.addWidget(port, 4, 0)
        self.select_port = create_combo_box()
        communication_setting_layout.addWidget(self.select_port, 4, 1)

        # 波特率（通信设置页）
        baud_rate = create_label("波特率:")
        communication_setting_layout.addWidget(baud_rate, 5, 0)
        self.set_baud_rate = create_combo_box(
            ["9600", "14400", "19200", "38400", "57600", "115200", "128000", "256000"], "115200"
        )
        communication_setting_layout.addWidget(self.set_baud_rate, 5, 1)

        # 串口连接按钮（通信设置页）
        self.serial_port_connect_button = create_button(style="")
        self.serial_port_connect_button.clicked.connect(self.toggle_serial_port_state)
        communication_setting_layout.addWidget(self.serial_port_connect_button, 6, 0, 1, 2)

        # 监听IP（通信设置页）
        listening_ip = create_label("监听IP:")
        communication_setting_layout.addWidget(listening_ip, 7, 0)
        self.set_listening_ip = create_line_edit("0.0.0.0")
        communication_setting_layout.addWidget(self.set_listening_ip, 7, 1)

        # 监听端口（通信设置页）
        listening_port = create_label("监听端口:")
        communication_setting_layout.addWidget(listening_port, 8, 0)
        self.set_listening_port = create_line_edit("32767")
        communication_setting_layout.addWidget(self.set_listening_port, 8, 1)

        # 客户端数量（通信设置页）
        client_count = create_label("客户端数量:")
        communication_setting_layout.addWidget(client_count, 9, 0)
        self.client_count_display = create_line_edit("0")
        self.client_count_display.setReadOnly(True)
        communication_setting_layout.addWidget(self.client_count_display, 9, 1)

        # TCP服务器启动按钮（通信设置页）
        self.tcp_server_button = create_button("打开TCP服务器", style="")
        self.tcp_server_button.clicked.connect(self.toggle_tcp_server_state)
        communication_setting_layout.addWidget(self.tcp_server_button, 10, 0, 1, 2)

        # UDP服务器启动按钮（通信设置页）
        self.udp_server_button = create_button("打开UDP服务器", style="")
        self.udp_server_button.clicked.connect(self.toggle_udp_server_state)
        communication_setting_layout.addWidget(self.udp_server_button, 11, 0, 1, 2)

        # WebSocket URI（通信设置页）
        ws_uri_label = create_label("WS地址:")
        communication_setting_layout.addWidget(ws_uri_label, 12, 0)
        self.set_ws_uri = create_line_edit(self.configuration.get("WebSocketURI", "ws://117.72.54.78:4001"))
        self.set_ws_uri.editingFinished.connect(lambda: self.configuration.set("WebSocketURI", self.set_ws_uri.text()))
        communication_setting_layout.addWidget(self.set_ws_uri, 12, 1)

        # WebSocket启动按钮（通信设置页）
        self.websocket_client_button = create_button("连接WebSocket", style="")
        self.websocket_client_button.clicked.connect(self.toggle_websocket_client_state)
        communication_setting_layout.addWidget(self.websocket_client_button, 13, 0, 1, 2)

        communication_setting_layout.setColumnStretch(0, 1)
        communication_setting_layout.setColumnStretch(1, 1)

        # ESP调试
        esp_debug = QWidget()
        esp_debug_layout = QGridLayout(esp_debug)
        esp_debug_layout.setVerticalSpacing(10)  # 设置行间距为 10 像素

        # SSID（ESP调试页）
        ssid = create_label("SSID:")
        esp_debug_layout.addWidget(ssid, 0, 0)
        self.set_ssid = create_line_edit(text=self.configuration["SSID"])
        self.set_ssid.editingFinished.connect(lambda: self.refresh_commands("SSID"))
        esp_debug_layout.addWidget(self.set_ssid, 0, 1)

        # Password（ESP调试页）
        password = create_label("Password:")
        esp_debug_layout.addWidget(password, 1, 0)
        self.set_password = create_line_edit(text=self.configuration["Password"])
        self.set_password.editingFinished.connect(lambda: self.refresh_commands("Password"))
        esp_debug_layout.addWidget(self.set_password, 1, 1)

        # IP（ESP调试页）
        local_ip = create_label("本机IP:")
        esp_debug_layout.addWidget(local_ip, 2, 0)
        ip = None
        for interface, addrs in psutil.net_if_addrs().items():
            if "vEthernet" in interface:  # 排除虚拟适配器，如包含 'vEthernet' 的适配器
                continue  # 跳过虚拟适配器
            if "wlan" in interface.lower() or "wi-fi" in interface.lower():  # 只匹配无线适配器接口名称（wlan 或 Wi-Fi）
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # 检查是否为 IPv4 地址
                        ip = addr.address
        if ip:
            self.set_local_ip = create_line_edit(ip)
        else:
            self.set_local_ip = create_line_edit("")
        self.set_local_ip.editingFinished.connect(lambda: self.refresh_commands("IP"))
        esp_debug_layout.addWidget(self.set_local_ip, 2, 1)

        # 选择指令（ESP调试页）
        command = create_label("选择指令")
        esp_debug_layout.addWidget(command, 3, 0)
        self.select_command = create_combo_box()
        esp_debug_layout.addWidget(self.select_command, 3, 1)

        # 指令发送按钮（ESP调试页）
        send_command_button = create_button("发送指令", style="")
        send_command_button.clicked.connect(self.send_command)
        esp_debug_layout.addWidget(send_command_button, 4, 0, 1, 2)

        # 串口输出面板（ESP调试页）
        self.output_panel = QTextEdit()
        self.output_panel.setReadOnly(True)
        self.output_panel.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.output_panel)
        scroll_area.setWidgetResizable(True)
        esp_debug_layout.addWidget(scroll_area, 5, 0, 1, 2)

        self.tab_widget.addTab(communication_setting, "通信设置")
        self.tab_widget.addTab(esp_debug, "ESP调试")
        layout.addWidget(self.tab_widget)

        self.set_content_layout(layout)

        self.update_ui()
        self.refresh_serial_ports()
        self.refresh_commands()

        # 定时更新通信状态
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(500)  # 每500ms触发一次

    def refresh_serial_ports(self):
        self.select_port.clear()
        ports = serial.tools.list_ports.comports()
        port_list = []
        for index, port in enumerate(ports):
            if "USB" in port.description or "USB" in port.hwid:
                port_type = "USB串口"
                port_list.append(f"{port.device} ({port_type})")

        self.select_port.addItems(port_list)

    def refresh_commands(self, item=None):
        if not item:
            self.select_command.clear()
            commands = [
                "AT",
                f'AT+CWJAP="{self.set_ssid.text()}","{self.set_password.text()}"',
                "AT+CIFSR",
                "AT+CWAUTOCONN=1",
                "AT+CIPMUX=0",
                "AT+CIPMODE=1",
                f'AT+CIPSTART="TCP","{self.set_local_ip.text()}",{self.set_listening_port.text()}',
                f'AT+CIPSTART="UDP","{self.set_local_ip.text()}",{self.set_listening_port.text()}',
                "AT+CIPSEND",
                "+++",
            ]
            self.select_command.addItems(commands)
        else:
            if item == "SSID" or item == "Password":
                if item == "SSID":
                    self.configuration["SSID"] = self.set_ssid.text()
                else:
                    self.configuration["Password"] = self.set_password.text()
                self.select_command.setItemText(1, f'AT+CWJAP="{self.set_ssid.text()}","{self.set_password.text()}"')
            elif item == "IP" or item == "Port":
                self.configuration["Password"] = self.set_password.text()
                self.select_command.setItemText(
                    5, f'AT+CIPSTART="TCP","{self.set_local_ip.text()}",{self.set_listening_port.text()}'
                )
                self.select_command.setItemText(
                    6, f'AT+CIPSTART="UDP","{self.set_local_ip.text()}",{self.set_listening_port.text()}'
                )

    def toggle_serial_port_state(self):
        if self.select_port.currentText() == "":
            QMessageBox.warning(self, "警告", "请先选择有效的USB串口！")
            return

        if self.communication_thread["串口"]:
            self.communication_thread["串口"].stop()
            self.communication_thread["串口"] = None
            self.serial_connect_state_display.setColor("Red")
            self.serial_port_connect_button.setText("打开串口")
            self.send_status.emit("串口已关闭！")
        else:
            self.serial_port_state_changed.emit(
                (self.select_port.currentText().split(" ")[0], self.set_baud_rate.currentText())
            )
            self.serial_connect_state_display.setColor("Green")
            self.serial_port_connect_button.setText("关闭串口")
            self.send_status.emit(f"串口{self.select_port.currentText().split(' ')[0]}已开启！")

    def toggle_tcp_server_state(self):
        if self.communication_thread["TCP"]:
            self.communication_thread["TCP"].stop()
            self.communication_thread["TCP"] = None
            self.tcp_server_state_display.setColor("Red")
            self.tcp_server_button.setText("打开TCP服务器")
            self.send_status.emit("TCP服务器已关闭！")
        else:
            self.tcp_server_state_changed.emit((self.set_listening_ip.text(), int(self.set_listening_port.text())))
            self.tcp_server_state_display.setColor("Green")
            self.tcp_server_button.setText("关闭TCP服务器")
            self.send_status.emit(
                f"TCP服务器已启动（正在监听{self.set_listening_ip.text()}:{self.set_listening_port.text()}）！"
            )

    def toggle_udp_server_state(self):
        if self.communication_thread["UDP"]:
            self.communication_thread["UDP"].stop()
            self.communication_thread["UDP"] = None
            self.udp_server_state_display.setColor("Red")
            self.udp_server_button.setText("打开UDP服务器")
            self.send_status.emit("UDP服务器已关闭！")
        else:
            self.udp_server_state_changed.emit((self.set_listening_ip.text(), int(self.set_listening_port.text())))
            self.udp_server_state_display.setColor("Green")
            self.udp_server_button.setText("关闭UDP服务器")
            self.send_status.emit(
                f"UDP服务器已启动（正在监听{self.set_listening_ip.text()}:{self.set_listening_port.text()}）！"
            )

    def toggle_websocket_client_state(self):
        if self.communication_thread.get("WS"):
            self.communication_thread["WS"].stop()
            self.communication_thread["WS"] = None
            self.websocket_client_state_display.setColor("Red")
            self.websocket_client_button.setText("连接WebSocket")
            self.send_status.emit("WebSocket连接已关闭！")
        else:
            uri = self.set_ws_uri.text()
            self.websocket_client_state_changed.emit((uri,))
            self.websocket_client_state_display.setColor("Green")
            self.websocket_client_button.setText("断开WebSocket")
            self.send_status.emit(f"正在连接WebSocket服务器({uri})...")

    def send_command(self):
        if not self.communication_thread["串口"] or not self.communication_thread["串口"].serial_connection.is_open:
            QMessageBox.warning(self, "警告", "串口异常，请检查串口连接状态！")
            return

        text = self.select_command.currentText()
        if text == "+++":
            self.communication_thread["串口"].serial_connection.write(
                (self.select_command.currentText()).encode("ascii", errors="ignore")
            )
        else:
            self.communication_thread["串口"].serial_connection.write(
                (self.select_command.currentText() + "\r\n").encode("ascii", errors="ignore")
            )
        self.update_output_panel(f"{self.select_command.currentText()}", "发送")
        self.communication_thread["串口"].serial_connection.flush()

    def update_output_panel(self, text, type="接收"):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.output_panel.append(f"{timestamp}({type}): {text}")

    def update_serial_connect_state(self):
        # 指示灯
        serial_obj = self.communication_thread.get("串口")
        if serial_obj and serial_obj.running:
            self.serial_connect_state_display.setColor("Green")
        else:
            self.serial_connect_state_display.setColor("Red")
            self.communication_thread["串口"] = None

        # 按钮
        if self.communication_thread["串口"]:
            self.serial_port_connect_button.setText("关闭串口")
        else:
            self.serial_port_connect_button.setText("打开串口")

        # 接收内容 - 更安全的信号管理
        serial_obj = self.communication_thread.get("串口")
        if serial_obj:
            # 检查是否已经连接过
            try:
                # 尝试断开连接，如果存在的话
                serial_obj.message_received.disconnect(self.update_output_panel)
            except (RuntimeError, TypeError):
                # 连接不存在或参数错误，忽略
                pass

            # 连接信号
            serial_obj.message_received.connect(self.update_output_panel)

    def update_tcp_server_state(self):
        # 指示灯
        if self.communication_thread["TCP"] and self.communication_thread["TCP"].running:
            self.tcp_server_state_display.setColor("Green")
        else:
            self.tcp_server_state_display.setColor("Red")
            self.communication_thread["TCP"] = None

        # 按钮
        if self.communication_thread["TCP"]:
            self.tcp_server_button.setText("关闭TCP服务器")
        else:
            self.tcp_server_button.setText("启动TCP服务器")

        # 客户端数量
        if self.communication_thread["TCP"]:
            self.client_count_display.setText(str(len(self.communication_thread["TCP"].clients)))
        else:
            self.client_count_display.setText("0")

    def update_udp_server_state(self):
        # 指示灯
        if self.communication_thread["UDP"] and self.communication_thread["UDP"].running:
            self.udp_server_state_display.setColor("Green")
        else:
            self.udp_server_state_display.setColor("Red")
            self.communication_thread["UDP"] = None

        # 按钮
        if self.communication_thread["UDP"]:
            self.udp_server_button.setText("关闭UDP服务器")
        else:
            self.udp_server_button.setText("启动UDP服务器")

    def update_websocket_client_state(self):
        # 指示灯
        if self.communication_thread.get("WS") and self.communication_thread["WS"].running:
            self.websocket_client_state_display.setColor("Green")
        else:
            self.websocket_client_state_display.setColor("Red")
            self.communication_thread["WS"] = None

        # 按钮
        if self.communication_thread.get("WS"):
            self.websocket_client_button.setText("断开WebSocket")
        else:
            self.websocket_client_button.setText("连接WebSocket")

    def update_ui(self):
        self.update_serial_connect_state()
        self.update_tcp_server_state()
        self.update_udp_server_state()
        self.update_websocket_client_state()
        self.refresh_serial_ports()
