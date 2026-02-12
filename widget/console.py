import datetime
import functools
import json
import os
import socket

import chardet
import pandas as pd
from openpyxl import Workbook
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from communication_threads.communication import (
    SerialPortThread,
    TcpServerThread,
    UdpServerThread,
    WebSocketClientThread,
)
from core.audio_manager import AudioManager
from core.config_manager import ConfigManager
from core.data_manager import DataManager
from core.web_server import WebServer
from widget.common import create_button, create_combo_box, create_label
from widget.dialog import (
    AddRecordDialog,
    CommunicationSettingDialog,
    CompetitionSettingDialog,
    InfoDialog,
    ModifyTimeDialog,
    PenaltySettingDialog,
    TimerSettingDialog,
)
from widget.screen import FullScreenWindow


class Console(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("北京科技大学智能汽车竞赛计时器控制台")

        # Responsive Window Size & Font Scaling
        screen = QGuiApplication.primaryScreen()
        rect = screen.availableGeometry()

        # Set window size to ~70% of screen
        target_width = int(rect.width() * 0.7)
        target_height = int(rect.height() * 0.7)
        self.setGeometry(
            (rect.width() - target_width) // 2, (rect.height() - target_height) // 2, target_width, target_height
        )

        # Calculate scale ratio (Base design: 1280x720)
        self.base_width = 1280.0
        self.base_height = 720.0

        # Initial calculation
        self._calculate_scale_ratio()

        # Initialize Core Managers
        self.config_manager = ConfigManager()
        self.data_manager = DataManager(self.config_manager)
        self.audio_manager = AudioManager()

        # Initialize Web Server
        self.web_server = WebServer()
        self.web_server.start()

        # UI State
        self.full_screen_window = None
        self.communication_thread = {
            "串口": None,
            "TCP": None,
            "UDP": None,
            "WS": None,
        }
        self.real_time = 0.0

        # Audio Paths
        self.audio_files = {
            "重置": os.path.abspath(os.path.join("audio", "reset.mp3")),
            "时间到": os.path.abspath(os.path.join("audio", "timeup.mp3")),
        }

        # Initialize UI
        self._init_ui()

        # Timer for countdown
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        # Initial Updates
        self.update_title_settings()
        self.update_record_option()
        self.update_team_information()
        self.update_timer_display()
        self.update_penalty_panel()

    def _calculate_scale_ratio(self):
        """Calculate scale ratio based on current window size"""
        # Use the smaller dimension ratio to ensure fit
        w_ratio = self.width() / self.base_width
        h_ratio = self.height() / self.base_height
        self.scale_ratio = max(0.8, min(w_ratio, h_ratio))

    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        self._calculate_scale_ratio()
        self._update_ui_styles()

    def _update_ui_styles(self):
        """Update fonts and sizes dynamically"""
        # Update Stylesheet
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #f5f6f7;
            }}
            QGroupBox {{
                font-weight: bold;
                font-size: {int(13 * self.scale_ratio)}px;
                border: 2px solid #dcdfe6;
                border-radius: 8px;
                margin-top: {int(12 * self.scale_ratio)}px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #409eff;
            }}
            QLabel {{
                color: #606266;
                font-size: {int(15 * self.scale_ratio)}px;
                font-weight: bold;
            }}
            QPushButton {{
                background-color: #409eff;
                color: white;
                border-radius: 4px;
                border: none;
                font-weight: bold;
                font-size: {int(13 * self.scale_ratio)}px;
            }}
            QPushButton:hover {{
                background-color: #66b1ff;
            }}
            QPushButton:pressed {{
                background-color: #3a8ee6;
            }}
            QPushButton#start_pause_btn {{
                background-color: #67c23a;
                font-size: {int(16 * self.scale_ratio)}px;
            }}
            QPushButton#start_pause_btn:hover {{
                background-color: #85ce61;
            }}
            QPushButton#player_enter_btn {{
                background-color: #626aef;
                font-size: {int(16 * self.scale_ratio)}px;
            }}
            QPushButton#player_enter_btn:hover {{
                background-color: #8590f2;
            }}
            QComboBox {{
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px;
                background: white;
                font-size: {int(12 * self.scale_ratio)}px;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)

        # Update Fonts for specific labels
        if hasattr(self, "race_label"):
            self.race_label.setFont(self._get_font(20, True))
            self.progress_display.setFont(self._get_font(12))
            self.team_id_display.setFont(self._get_font(12, True))
            self.team_name_display.setFont(self._get_font(12, True))
            self.team_members_display.setFont(self._get_font(11))

            self.race_phase_display.setFont(self._get_font(16, True))
            self.remaining_time_display.setFont(self._get_font(24, True))
            self.real_time_display.setFont(self._get_font(24, True))

            self.best_record_display.setFont(self._get_font(14, True))
            self.next_team_display.setFont(self._get_font(12))

            # Update Button Heights
            btn_height = int(50 * self.scale_ratio)
            self.start_and_pause_button.setFixedHeight(btn_height)
            self.modify_button.setFixedHeight(btn_height)
            if hasattr(self, "player_enter_button"):
                self.player_enter_button.setFixedHeight(btn_height)

            combo_height = int(35 * self.scale_ratio)
            self.record_option_display.setFixedHeight(combo_height)

    def _get_font(self, size, bold=False):
        """Get scaled font"""
        scaled_size = int(size * self.scale_ratio)
        font = QFont("Microsoft YaHei")
        font.setPointSize(scaled_size)
        if bold:
            font.setBold(True)
        return font

    def _init_ui(self):
        # Create Menu Bar
        self._create_menu_bar()

        # Create Status Bar
        self.status_bar = self.statusBar()

        # Set Stylesheet
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #f5f6f7;
            }}
            QGroupBox {{
                font-weight: bold;
                font-size: {int(13 * self.scale_ratio)}px;
                border: 2px solid #dcdfe6;
                border-radius: 8px;
                margin-top: {int(12 * self.scale_ratio)}px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #409eff;
            }}
            QLabel {{
                color: #606266;
            }}
            QPushButton {{
                background-color: #409eff;
                color: white;
                border-radius: 4px;
                border: none;
                font-weight: bold;
                font-size: {int(13 * self.scale_ratio)}px;
            }}
            QPushButton:hover {{
                background-color: #66b1ff;
            }}
            QPushButton:pressed {{
                background-color: #3a8ee6;
            }}
            QPushButton#start_pause_btn {{
                background-color: #67c23a;
                font-size: {int(16 * self.scale_ratio)}px;
            }}
            QPushButton#start_pause_btn:hover {{
                background-color: #85ce61;
            }}
            QComboBox {{
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px;
                background: white;
                font-size: {int(12 * self.scale_ratio)}px;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)

        # Main Layout
        central_widget = QWidget()
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area for resolution independence
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        inner_widget = QWidget()
        main_layout = QVBoxLayout(inner_widget)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(15)

        # 1. Race Header
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.race_label = create_label(font=self._get_font(20, True), style="color: #303133; padding: 10px 0px;")
        self.race_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.race_label)

        main_layout.addWidget(header_container)

        # 2. Main Content Area (Horizontal)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # Left Side: Team & Time Info
        left_side = QVBoxLayout()
        left_side.setSpacing(15)

        # Team Info Group
        team_group = QGroupBox("当前队伍信息")
        team_group.setMinimumWidth(int(500 * self.scale_ratio))
        team_layout = QGridLayout(team_group)
        team_layout.setContentsMargins(15, 25, 15, 15)
        team_layout.setSpacing(10)

        headers = ["比赛进度", "队伍编号", "队伍名称", "队伍成员"]
        self.progress_display = create_label(font=self._get_font(12))
        self.team_id_display = create_label(font=self._get_font(12, True))
        self.team_name_display = create_label(font=self._get_font(12, True))
        self.team_members_display = create_label(font=self._get_font(11))

        for i, header in enumerate(headers):
            team_layout.addWidget(create_label(header, style="color: #909399;"), 0, i)

        team_layout.addWidget(self.progress_display, 1, 0)
        team_layout.addWidget(self.team_id_display, 1, 1)
        team_layout.addWidget(self.team_name_display, 1, 2)
        team_layout.addWidget(self.team_members_display, 1, 3)
        left_side.addWidget(team_group)

        # Time Info Group
        time_group = QGroupBox("比赛计时状态")
        time_layout = QGridLayout(time_group)
        time_layout.setContentsMargins(15, 20, 15, 15)

        time_layout.addWidget(create_label("当前阶段", font=self._get_font(11)), 0, 0)
        self.race_phase_display = create_label(font=self._get_font(16, True), style="color: #e6a23c;")
        time_layout.addWidget(self.race_phase_display, 1, 0)

        time_layout.addWidget(create_label("剩余时间", font=self._get_font(11)), 0, 1)
        self.remaining_time_display = create_label(font=self._get_font(24, True), style="color: #f56c6c;")
        time_layout.addWidget(self.remaining_time_display, 1, 1)

        time_layout.addWidget(create_label("实时成绩", font=self._get_font(11)), 0, 2)
        self.real_time_display = create_label("0.000s", font=self._get_font(24, True), style="color: #409eff;")
        time_layout.addWidget(self.real_time_display, 1, 2)

        # Control Buttons
        btn_layout = QHBoxLayout()
        self.start_and_pause_button = create_button("开始倒计时")
        self.start_and_pause_button.setObjectName("start_pause_btn")
        self.start_and_pause_button.setFixedHeight(int(50 * self.scale_ratio))
        self.start_and_pause_button.clicked.connect(self.toggle_start_and_pause_button)

        self.modify_button = create_button("修改剩余时间")
        self.modify_button.setFixedHeight(int(50 * self.scale_ratio))
        self.modify_button.clicked.connect(functools.partial(self.open_dialog, "修改剩余时间"))

        self.player_enter_button = create_button("选手入场")
        self.player_enter_button.setObjectName("player_enter_btn")
        self.player_enter_button.setFixedHeight(int(50 * self.scale_ratio))
        self.player_enter_button.clicked.connect(self.switch_to_race_stage)

        btn_layout.addWidget(self.start_and_pause_button, 2)
        btn_layout.addWidget(self.player_enter_button, 1)
        btn_layout.addWidget(self.modify_button, 1)
        time_layout.addLayout(btn_layout, 2, 0, 1, 3)

        left_side.addWidget(time_group)

        # Next Team & Best Record
        extra_group = QGroupBox("比赛数据")
        extra_layout = QVBoxLayout(extra_group)
        extra_layout.setContentsMargins(15, 25, 15, 15)
        extra_layout.setSpacing(10)

        # Data Info Row
        data_info_layout = QHBoxLayout()

        # Best Record
        best_record_container = QVBoxLayout()
        best_record_container.addWidget(create_label("最好成绩", alignment=Qt.AlignCenter))
        self.best_record_display = create_label(font=self._get_font(14, True), alignment=Qt.AlignCenter)
        best_record_container.addWidget(self.best_record_display)
        data_info_layout.addLayout(best_record_container)

        # Next Team
        next_team_container = QVBoxLayout()
        next_team_container.addWidget(create_label("下支队伍", alignment=Qt.AlignCenter))
        self.next_team_display = create_label(font=self._get_font(12), alignment=Qt.AlignCenter)
        next_team_container.addWidget(self.next_team_display)
        data_info_layout.addLayout(next_team_container)

        extra_layout.addLayout(data_info_layout)

        # Separator Line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #dcdfe6;")
        extra_layout.addWidget(line)

        # Navigation Buttons Row
        nav_btn_layout = QHBoxLayout()
        self.previous_team_button = create_button("切换上支队伍")
        self.next_team_button = create_button("切换下支队伍")

        btn_height = int(40 * self.scale_ratio)
        self.previous_team_button.setFixedHeight(btn_height)
        self.next_team_button.setFixedHeight(btn_height)

        self.previous_team_button.clicked.connect(self.switch_to_previous_team)
        self.next_team_button.clicked.connect(self.switch_to_next_team)

        nav_btn_layout.addWidget(self.previous_team_button)
        nav_btn_layout.addWidget(self.next_team_button)
        extra_layout.addLayout(nav_btn_layout)

        left_side.addWidget(extra_group)

        content_layout.addLayout(left_side, 2)

        # Right Side: Score & Penalty
        right_side = QVBoxLayout()

        score_group = QGroupBox("成绩管理")
        score_layout = QVBoxLayout(score_group)

        self.record_option_display = create_combo_box()
        self.record_option_display.setFixedHeight(int(35 * self.scale_ratio))
        self.record_option_display.setEditable(True)
        self.record_option_display.lineEdit().setReadOnly(True)
        self.record_option_display.lineEdit().setAlignment(Qt.AlignCenter)
        score_layout.addWidget(self.record_option_display)

        score_btn_grid = QGridLayout()
        self.confirm_record_button = create_button("确认成绩")
        self.cancel_record_button = create_button("作废成绩")
        self.add_record_button = create_button("手动添加")

        self.confirm_record_button.clicked.connect(functools.partial(self.update_record_state, "已确认"))
        self.cancel_record_button.clicked.connect(functools.partial(self.update_record_state, "已作废"))
        self.add_record_button.clicked.connect(functools.partial(self.open_dialog, "添加比赛成绩"))

        score_btn_grid.addWidget(self.confirm_record_button, 0, 0)
        score_btn_grid.addWidget(self.cancel_record_button, 0, 1)
        score_btn_grid.addWidget(self.add_record_button, 1, 0, 1, 2)
        score_layout.addLayout(score_btn_grid)

        # Applied Penalties
        score_layout.addWidget(create_label("已扣罚项 (点击删除)", style="margin-top: 10px; color: #909399;"))
        left_scroll_area = QScrollArea()
        left_widget = QWidget()
        self.left_layout = QGridLayout(left_widget)  # Changed to Grid
        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_scroll_area.setWidget(left_widget)
        left_scroll_area.setWidgetResizable(True)
        score_layout.addWidget(left_scroll_area)

        right_side.addWidget(score_group, 3)

        penalty_group = QGroupBox("快速罚时面板")
        penalty_layout = QVBoxLayout(penalty_group)
        right_scroll_area = QScrollArea()
        right_widget = QWidget()
        self.right_layout = QGridLayout(right_widget)  # Changed to Grid
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_scroll_area.setWidget(right_widget)
        right_scroll_area.setWidgetResizable(True)
        penalty_layout.addWidget(right_scroll_area)

        right_side.addWidget(penalty_group, 2)

        content_layout.addLayout(right_side, 1)
        main_layout.addLayout(content_layout)

        scroll_area.setWidget(inner_widget)
        outer_layout.addWidget(scroll_area)

        self.setCentralWidget(central_widget)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("文件")

        import_action = QAction("导入抽签结果", self)
        import_action.triggered.connect(self.import_team_list)
        file_menu.addAction(import_action)

        save_action = QAction("保存比赛结果", self)
        save_action.triggered.connect(self.save_team_list)
        file_menu.addAction(save_action)

        # Settings Menu
        set_menu = menu_bar.addMenu("设置")

        settings_actions = [
            ("通信设置", self.open_dialog),
            ("比赛设置", self.open_dialog),
            ("计时设置", self.open_dialog),
            ("罚时设置", self.open_dialog),
        ]

        for name, slot in settings_actions:
            action = QAction(name, self)
            action.triggered.connect(functools.partial(slot, name))
            set_menu.addAction(action)

        # Project Menu
        project_menu = menu_bar.addMenu("投屏")
        project_menu.aboutToShow.connect(self.update_project_menu)
        project_menu.setObjectName("投屏")

        # About
        about_action = menu_bar.addAction("关于")
        about_action.triggered.connect(self.show_about)

    def broadcast_current_state(self):
        current_team = self.data_manager.get_current_team()

        # Get next team info
        current_index = self.data_manager.get_current_team_index()
        team_list = self.data_manager.get_team_list()
        next_team_text = "无"
        if current_index + 1 < len(team_list):
            next_team = team_list[current_index + 1]
            next_team_text = f"{next_team['队伍编号']} {next_team['队伍名称']}"

        data = {
            "比赛名称": self.config_manager.get("比赛名称"),
            "比赛组别": self.config_manager.get("比赛组别"),
            "比赛阶段": self.race_phase_display.text(),
            "比赛进度": self.progress_display.text(),
            "队伍编号": str(current_team.get("队伍编号", "---")),
            "队伍名称": current_team.get("队伍名称", "---"),
            "队伍成员": current_team.get("队伍成员", "---"),
            "剩余时间": self.remaining_time_display.text(),
            "实时成绩": self.real_time_display.text(),
            "最好成绩": self.best_record_display.text(),
            "下支队伍": next_team_text,
        }
        self.web_server.broadcast(data)

        # Remote WS (from main feature)
        ws_data = current_team.copy()
        ws_data["Key"] = self.config_manager.get("Key", "")
        if self.communication_thread.get("WS"):
            try:
                json_str = json.dumps(ws_data, ensure_ascii=False)
                self.communication_thread["WS"].send_message(json_str)
            except Exception:
                pass

    def update_status(self, message):
        self.status_bar.showMessage(f"{datetime.datetime.now().strftime('%H:%M:%S')}: {message}", 0)

    def _show_warning(self, message):
        InfoDialog("警告", message, self).exec()

    def update_full_screen_display(self, widget_name, text):
        if self.full_screen_window:
            widget = getattr(self.full_screen_window, widget_name, None)
            if widget and widget.text() != text:
                widget.setText(text)

    def switch_to_race_stage(self):
        """Switch from Pre-race to Race stage immediately"""
        current_team = self.data_manager.get_current_team()
        if not current_team:
            return

        if current_team["比赛阶段"] == "赛前准备阶段":
            # Update State
            current_team["比赛阶段"] = "正式比赛阶段"

            # Reset Timer
            race_time = self.config_manager.get("比赛时间")
            current_team["剩余时间"] = race_time
            current_team["是否暂停"] = True  # Start paused? or Running? Usually paused waiting for start

            # Reset Real Time
            self.real_time_display.setText("0.000s")

            # Update UI
            self.update_timer_display()
            self.update_status(f"队伍 {current_team['队伍名称']} 已进入正式比赛阶段")
            self.broadcast_current_state()
        else:
            self._show_warning("当前不是赛前准备阶段，无法执行入场操作！")

    def import_team_list(self):
        if self.data_manager.get_current_team_index() > 0:
            self._show_warning("当前已开始比赛，请先清空队伍名单后再导入！")
            return

        file_name, _ = QFileDialog.getOpenFileName(
            self, "导入队伍名单", "", "Excel Files (*.xls *.xlsx);;CSV Files (*.csv);;All Files (*)"
        )

        if not file_name:
            return

        try:
            if file_name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_name, header=None)
            elif file_name.endswith(".csv"):
                # Detect encoding
                with open(file_name, "rb") as f:
                    result = chardet.detect(f.read())
                encoding = result["encoding"] or "utf-8"

                try:
                    df = pd.read_csv(file_name, encoding=encoding, header=None)
                except Exception:
                    # Fallback encodings
                    for enc in ["utf-8", "gbk", "gb2312"]:
                        try:
                            df = pd.read_csv(file_name, encoding=enc, header=None)
                            break
                        except Exception:
                            continue
                    else:
                        raise ValueError("无法使用任何编码读取文件。")
            else:
                self._show_warning("不支持的文件格式！")
                return

            team_list = []
            for index, row in df.iterrows():
                # Filter out NaN/None from team members
                team_members = [str(member) for member in row.iloc[2:6] if pd.notna(member)]
                team = {
                    "队伍编号": row.iloc[0],
                    "队伍名称": row.iloc[1],
                    "队伍成员": "、".join(team_members),
                    "比赛阶段": "赛前准备阶段",
                    "剩余时间": self.config_manager.get("赛前准备时间"),
                    "是否暂停": True,
                    "所有成绩": [],
                    "最好成绩": 999.999,
                }
                team_list.append(team)

            # Append to existing list (skipping index 0 which is Test team if needed, or just append)
            # Original code appended to existing list.
            current_list = self.data_manager.get_team_list()
            current_list.extend(team_list)
            self.data_manager.set_current_team_index(1)  # Start from first imported team?

            self.update_status(f"读取文件 {file_name} 成功！")
            self.update_team_information()
            self.update_timer_display()
            self.update_record_option()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件时出错：{e}")

    def save_team_list(self):
        if self.data_manager.get_current_team_index() == 0:
            self._show_warning("当前未开始比赛，无法保存比赛结果！")
            return

        filename, _ = QFileDialog.getSaveFileName(None, "保存文件", "比赛结果", "Excel Files (*.xlsx);;All Files (*)")

        if filename:
            try:
                workbook = Workbook()
                sheet = workbook.active
                sheet.title = "队伍信息"
                headers = ["队伍编号", "队伍名称", "最好成绩"]
                sheet.append(headers)

                for team in self.data_manager.get_team_list()[1:]:  # Skip test team?
                    row_data = [
                        team["队伍编号"],
                        team["队伍名称"],
                        team["最好成绩"],
                    ]
                    sheet.append(row_data)

                workbook.save(filename)
                self.update_status(f"文件已保存到: {filename}")
            except Exception as e:
                self._show_warning(f"保存失败: {e}")

    def open_dialog(self, dialog_type, checked=False):
        current_team = self.data_manager.get_current_team()
        progress = self.data_manager.get_current_team_index()
        config = self.config_manager.config

        dialog = None

        if dialog_type == "通信设置":
            dialog = CommunicationSettingDialog(config, self.communication_thread)
            dialog.serial_port_state_changed.connect(self.open_serial_port)
            dialog.tcp_server_state_changed.connect(self.open_tcp_server)
            dialog.udp_server_state_changed.connect(self.open_udp_server)
            dialog.websocket_client_state_changed.connect(self.open_websocket_client)
            dialog.send_status.connect(self.update_status)
        elif dialog_type == "比赛设置":
            dialog = CompetitionSettingDialog(config)
            dialog.setting_saved.connect(self.update_title_settings)
        elif dialog_type == "计时设置":
            dialog = TimerSettingDialog(config, progress)
        elif dialog_type == "罚时设置":
            dialog = PenaltySettingDialog(config)
            dialog.setting_saved.connect(self.update_penalty_panel)
        elif dialog_type == "修改剩余时间":
            if current_team["是否暂停"]:
                dialog = ModifyTimeDialog(current_team)
                dialog.setting_saved.connect(self.update_timer_display)
            else:
                self._show_warning("请先暂停再修改剩余时间！")
                return
        elif dialog_type == "添加比赛成绩":
            dialog = AddRecordDialog(current_team)
            dialog.setting_saved.connect(self.update_record_option)

        if dialog:
            dialog.exec()

    def open_serial_port(self, config):
        self.communication_thread["串口"] = SerialPortThread(config[0], config[1])
        self._connect_communication_signals(self.communication_thread["串口"])
        self.communication_thread["串口"].start()

    def open_tcp_server(self, config):
        self.communication_thread["TCP"] = TcpServerThread(config[0], config[1])
        self._connect_communication_signals(self.communication_thread["TCP"])
        self.communication_thread["TCP"].start()

    def open_udp_server(self, config):
        self.communication_thread["UDP"] = UdpServerThread(config[0], config[1])
        self._connect_communication_signals(self.communication_thread["UDP"])
        self.communication_thread["UDP"].start()

    def open_websocket_client(self, config):
        self.communication_thread["WS"] = WebSocketClientThread(config[0])
        self._connect_communication_signals(self.communication_thread["WS"])
        self.communication_thread["WS"].start()
        self.update_status(f"WebSocket客户端已启动，正在连接 {config[0]}...")
        # Update config
        self.config_manager.set("WebSocketURI", config[0])

    def _connect_communication_signals(self, thread):
        thread.real_received.connect(self.update_real_time_display)
        thread.final_received.connect(self.add_record)
        thread.send_status.connect(self.update_status)
        thread.timer_reset.connect(functools.partial(self.audio_play, "重置"))

    def update_title_settings(self):
        config = self.config_manager.config
        title_text = config["比赛名称"] + config["比赛阶段"] + config["比赛组别"]
        self.race_label.setText(title_text)

        if self.full_screen_window:
            self.update_full_screen_display("title", config["比赛名称"] + config["比赛阶段"])
            self.update_full_screen_display("subheading", config["比赛组别"])

    def update_project_menu(self):
        project_menu = self.menuBar().findChild(QMenu, "投屏")
        if not project_menu:
            return

        project_menu.clear()

        # Web Projection
        web_action = QAction("打开网页投屏 (浏览器)", self)
        web_action.triggered.connect(self.open_web_projection)
        project_menu.addAction(web_action)
        project_menu.addSeparator()

        screens = QGuiApplication.screens()

        for i, screen in enumerate(screens):
            action = QAction(f"显示器 {i + 1}: {screen.name()}", self)
            action.setCheckable(True)
            action.triggered.connect(functools.partial(self.project_to_screen, i))
            project_menu.addAction(action)

    def open_web_projection(self):
        # Open localhost in default browser
        QDesktopServices.openUrl(QUrl("http://localhost:8000"))

        # Get Local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception:
            ip = "127.0.0.1"

        InfoDialog(
            "网页投屏已启动",
            f"网页投屏正在运行。<br><br>"
            f"本机访问: <a href='http://localhost:8000'>http://localhost:8000</a><br>"
            f"局域网访问: <a href='http://{ip}:8000'>http://{ip}:8000</a><br><br>"
            f"请确保防火墙允许访问端口 8000。",
            self,
        ).exec()

    def project_to_screen(self, screen_index):
        if self.full_screen_window and self.full_screen_window.screen() == QApplication.screens()[screen_index]:
            self.full_screen_window.close()
            self.full_screen_window = None
            return

        if self.full_screen_window:
            self.full_screen_window.close()

        self.full_screen_window = FullScreenWindow(self.config_manager.config, self.data_manager.race_data)
        screens = QApplication.screens()

        if 0 <= screen_index < len(screens):
            # 将全屏窗口移到指定的屏幕，始终全屏显示
            target_screen = screens[screen_index]
            screen_geometry = target_screen.geometry()
            self.full_screen_window.setGeometry(screen_geometry)
            self.full_screen_window.showFullScreen()
            self.update_team_information()
            self.update_timer_display()

    def show_about(self):
        InfoDialog(
            "关于",
            """
            <div style='text-align: center;'>
            <h2>北京科技大学智能汽车竞赛计时器</h2>
            <p>作者：谢翔远</p>
            <p>日期：2026年2月12日</p>
            <p>版本：V2.0</p>
            <p><i>轮到你，为世界加速！</i></p>
            """,
            self,
        ).exec()

    def update_team_information(self):
        current_team = self.data_manager.get_current_team()
        progress = self.data_manager.get_current_team_index()
        total_teams = len(self.data_manager.get_team_list()) - 1  # Excluding test team?

        self.progress_display.setText(f"{progress}/{total_teams}")

        if self.full_screen_window:
            self.update_full_screen_display("progress_display", f"{progress}/{total_teams}")

        self.team_id_display.setText(current_team.get("队伍编号", "Null"))
        self.update_full_screen_display("team_id_display", current_team.get("队伍编号", "Null"))

        self.team_name_display.setText(current_team.get("队伍名称", "Null"))
        self.update_full_screen_display("team_name_display", current_team.get("队伍名称", "Null"))

        self.team_members_display.setText(current_team.get("队伍成员", "Null"))
        self.update_full_screen_display("team_members_display", current_team.get("队伍成员", "Null"))

        # Next Team
        team_list = self.data_manager.get_team_list()
        if progress + 1 < len(team_list):
            next_team = team_list[progress + 1]
            next_team_text = f"{next_team['队伍编号']}：{next_team['队伍名称']}"
        else:
            next_team_text = "无"

        self.next_team_display.setText(next_team_text)
        self.update_full_screen_display("next_team_display", next_team_text)

        if progress > 0:
            self.update_timer_display()

        if self.full_screen_window:
            self.full_screen_window.update()

        self.broadcast_current_state()

    def update_real_time_display(self, time):
        formatted_time = f"{time:.3f}s"
        self.real_time_display.setText(formatted_time)
        self.update_full_screen_display("real_time_display", formatted_time)
        self.broadcast_current_state()

    def update_timer(self):
        current_team = self.data_manager.get_current_team()
        if current_team["是否暂停"]:
            return

        current_team["剩余时间"] -= 1

        if current_team["剩余时间"] <= 0:
            if current_team["比赛阶段"] == "赛前准备阶段":
                current_team["比赛阶段"] = "正式比赛阶段"
                current_team["剩余时间"] = self.config_manager.get("比赛时间")
            else:
                current_team["剩余时间"] = 0
                self.audio_play("时间到")
                self.toggle_start_and_pause_button()

        self.update_timer_display()

    def update_timer_display(self):
        current_team = self.data_manager.get_current_team()

        race_stage = current_team.get("比赛阶段", "未知比赛阶段")
        self.race_phase_display.setText(race_stage)
        self.update_full_screen_display("race_phase_display", race_stage)

        remaining_time = current_team.get("剩余时间", None)
        if remaining_time is not None:
            if remaining_time < 60:
                time_text = f"{remaining_time} 秒"
            else:
                minutes = remaining_time // 60
                seconds = remaining_time % 60
                time_text = f"{minutes} 分 {seconds} 秒"
            self.remaining_time_display.setText(time_text)
            self.update_full_screen_display("remaining_time_display", time_text)

            # WebSocket Broadcast
            progress = self.data_manager.get_current_team_index()
            team_list = self.data_manager.get_team_list()
            if 0 <= progress < len(team_list):
                team_data = {**team_list[progress], "Key": self.config_manager.get("Key")}
                json_str = json.dumps(team_data, ensure_ascii=False, indent=2)
                if self.communication_thread["WS"] is not None:
                    self.communication_thread["WS"].send_message(json_str)
        else:
            self.remaining_time_display.setText("Null")
            self.update_full_screen_display("remaining_time_display", "Null")

        best_record = current_team.get("最好成绩", "Null")
        self.best_record_display.setText(f"{best_record}s")
        self.update_full_screen_display("best_record_display", f"{best_record}s")

        if self.full_screen_window:
            self.full_screen_window.update()

        self.broadcast_current_state()

    def toggle_start_and_pause_button(self):
        current_team = self.data_manager.get_current_team()
        current_team["是否暂停"] = not current_team["是否暂停"]
        button_text = "开始倒计时" if current_team["是否暂停"] else "暂停倒计时"
        self.start_and_pause_button.setText(button_text)

    def switch_to_previous_team(self):
        if self.check_unprocessed_scores():
            return

        if not self.data_manager.previous_team():
            self._show_warning("当前已经是第一支队伍！")
        else:
            self._on_team_switch()

    def switch_to_next_team(self):
        if self.check_unprocessed_scores():
            return

        if not self.data_manager.next_team():
            self._show_warning("当前已经是最后一支队伍！")
        else:
            self._on_team_switch()

    def _on_team_switch(self):
        self.update_team_information()
        self.update_record_option()
        self.update_penalty_panel()
        self.update_penalty_area()

    def check_unprocessed_scores(self):
        current_team = self.data_manager.get_current_team()
        for data in current_team["所有成绩"]:
            if data["状态"] == "未处理":
                self._show_warning("还有成绩未处理，请将所有成绩处理完毕后再切换队伍！")
                return True

        if not current_team["是否暂停"]:
            self._show_warning("请将比赛暂停后再调整比赛进度！")
            return True

        return False

    def update_record_option(self):
        current_team = self.data_manager.get_current_team()
        all_records = current_team["所有成绩"]

        old_index = self.record_option_display.currentIndex()
        if old_index < 0:
            old_index = 0

        self.record_option_display.clear()

        if all_records:
            for data in all_records:
                total_penalty = sum(penalty[1] for penalty in data["罚时"])
                self.record_option_display.addItem(f"{data['原始时间']:.3f}+{total_penalty} ({data['状态']})")

            self.record_option_display.setCurrentIndex(min(old_index, len(all_records) - 1))

            for i in range(self.record_option_display.count()):
                self.record_option_display.setItemData(
                    i, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole
                )
        else:
            self.record_option_display.addItem("暂无成绩")
            self.record_option_display.setItemData(0, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole)

        # Update penalty area for the selected record
        self.update_penalty_area()

    def update_record_state(self, status_text):
        if self.record_option_display.currentText() == "暂无成绩":
            self._show_warning("请先选中一个成绩再进行操作！")
            return

        index = self.record_option_display.currentIndex()
        current_team = self.data_manager.get_current_team()

        current_team["所有成绩"][index]["状态"] = status_text
        self.update_record_option()

        # Update best record
        valid_times = [data["修正时间"] for data in current_team["所有成绩"] if data["状态"] == "已确认"]
        best_record = min(valid_times, default=999.999)
        current_team["最好成绩"] = best_record
        self.best_record_display.setText(f"{best_record:.3f}s")

        # Broadcast update
        self.broadcast_current_state()

    def add_record(self, time):
        current_team = self.data_manager.get_current_team()
        current_team["所有成绩"].append(
            {
                "原始时间": time,
                "修正时间": time,
                "状态": "未处理",
                "罚时": [],
            }
        )
        self.update_record_option()
        self.update_status("成绩有更新，请及时处理！")

    def refresh_penalty_area(self):
        # Clear existing
        while self.left_layout.count():
            item = self.left_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        current_team = self.data_manager.get_current_team()
        if not current_team:
            return

        current_record_idx = self.record_option_display.currentIndex()
        if current_record_idx < 0 or current_record_idx >= len(current_team["所有成绩"]):
            # Even if no record selected, we might want to show available penalties (right side)
            pass
        else:
            current_record = current_team["所有成绩"][current_record_idx]

            # Left: Applied Penalties
            row = 0
            col = 0
            # Using original data structure: list of (text, value) tuples
            for i, (p_name, p_val) in enumerate(current_record.get("罚时", [])):
                btn = QPushButton(f"{p_name} (x)")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #fef0f0;
                        color: #f56c6c;
                        border: 1px solid #fbc4c4;
                        border-radius: 4px;
                        padding: 5px;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #fde2e2;
                    }
                """)
                btn.setFont(self._get_font(12))
                # Connect to remove_penalty with index
                btn.clicked.connect(lambda checked, idx=i: self.remove_penalty(idx))

                self.left_layout.addWidget(btn, row, col)
                col += 1
                if col > 1:  # 2 columns
                    col = 0
                    row += 1

        # Right: Available Penalties
        # Using original data structure: list of (text, value) tuples
        penalty_types = self.config_manager.get("罚时种类")
        row = 0
        col = 0
        for text, value in penalty_types:
            btn = QPushButton(f"{text}\n+{value}s")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f9eb;
                    color: #67c23a;
                    border: 1px solid #c2e7b0;
                    border-radius: 4px;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #e1f3d8;
                }
            """)
            btn.setFont(self._get_font(12))
            btn.clicked.connect(lambda checked, name=text, val=value: self.add_penalty(name, val))

            self.right_layout.addWidget(btn, row, col)
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1

    # Compatibility wrappers
    def update_penalty_panel(self):
        self.refresh_penalty_area()

    def update_penalty_area(self):
        self.refresh_penalty_area()

    def add_penalty(self, text, value):
        if self.record_option_display.currentText() == "暂无成绩":
            self._show_warning("当前未选中任何成绩，不能添加罚时！")
            return

        index = self.record_option_display.currentIndex()
        current_team = self.data_manager.get_current_team()
        current_record = current_team["所有成绩"][index]

        if current_record["状态"] == "已确认":
            self._show_warning("本次成绩已确认，不能添加罚时！")
            return

        current_record["罚时"].append((text, value))

        total_penalty = sum(p[1] for p in current_record["罚时"])
        current_record["修正时间"] = current_record["原始时间"] + total_penalty

        self.update_record_option()

    def remove_penalty(self, penalty_index):
        index = self.record_option_display.currentIndex()
        current_team = self.data_manager.get_current_team()
        current_record = current_team["所有成绩"][index]

        if current_record["状态"] == "已确认":
            self._show_warning("本次成绩已确认，不能撤销罚时！")
            return

        if 0 <= penalty_index < len(current_record["罚时"]):
            del current_record["罚时"][penalty_index]

            # Recalculate time
            total_penalty = sum(p[1] for p in current_record["罚时"])
            current_record["修正时间"] = current_record["原始时间"] + total_penalty

            self.update_record_option()

    def audio_play(self, audio_type):
        path = self.audio_files.get(audio_type)
        if path:
            self.audio_manager.play(path)
            if audio_type == "重置":
                self.update_status("计时器已手动重置！")
                self.update_real_time_display(0)
            else:
                self.update_status("当前队伍比赛时间结束！")
