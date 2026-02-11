import json
import os

import chardet
from PySide6.QtGui import QGuiApplication, QAction
from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QMainWindow, QMenu, QApplication
from openpyxl import Workbook

from task_thread import *
from widget.dialog import *
from widget.screen import *


class Console(QMainWindow):
    # 组别到Key的映射关系（统一管理，避免重复定义）
    GROUP_KEY_MAPPING = {
        "摄像头组": "220dfce992d21aea4507065760ddfce7",
        "电磁组": "46840a1abb9fa373fe8daa1991bd53cd",
        "缩微光电组": "141d48c6c30c722025d1e75e1fafcb87"
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("北京科技大学智能汽车竞赛计时器控制台 V2.0")
        self.setGeometry(100, 100, 900, 600)
        self.full_screen_window = None
        self.communication_thread = {
            "串口": None,
            "TCP": None,
            "UDP": None,
            "WS": None,
        }
        self.real_time = 0
        self.audio_path = {
            "重置": search_file("reset.mp3"),
            "时间到": search_file("timeup.mp3")
        }

        # 默认配置文件
        self.default_configuration = {
            "比赛名称": "北京科技大学智能汽车竞赛",
            "比赛阶段": "第二次分站赛",
            "比赛组别": "摄像头组",
            "速度计算": False,
            "赛道长度": 0,
            "赛前准备时间": 90,
            "比赛时间": 600,
            "罚时种类": [
                ("停车失败", -10),
                ("碰撞小型路障", -10)
            ],
            "SSID": "LAPTOP-LYL",
            "Password": "idol0920",
            "Key": "",
            "投屏缩放比例": 1.0  # 投屏分辨率缩放比例，默认1.0（100%）
        }

        # 读取配置文件
        try:
            with open("config.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                if "罚时种类" in data and isinstance(data["罚时种类"], list):
                    data["罚时种类"] = [tuple(item) if isinstance(item, list) else item for item in data["罚时种类"]]
                self.configuration = data
        except Exception:
            self.configuration = self.default_configuration
            self._show_warning("读取配置文件失败，将使用默认配置！")
            # 打印默认key值
            print(f"使用默认配置: 组别={self.configuration['比赛组别']}, Key={self.configuration['Key']}")

        # 根据比赛组别自动配置Key（在检查缺失配置之前执行，确保Key始终与组别匹配）
        # 即使JSON文件中的Key错误，也会根据组别自动更新为正确的Key
        group_name = self.configuration.get("比赛组别", "")
        if group_name in self.GROUP_KEY_MAPPING:
            old_key = self.configuration.get("Key", "未设置")
            self.configuration["Key"] = self.GROUP_KEY_MAPPING[group_name]
            if old_key != self.configuration["Key"]:
                print(f"根据组别自动更新Key: 组别={group_name}, 旧Key={old_key}, 新Key={self.configuration['Key']}")
            else:
                print(f"根据组别自动配置Key: 组别={group_name}, Key={self.configuration['Key']}")

        # 检查配置文件
        missing_config = []
        for key in self.default_configuration:
            if key not in self.configuration:
                self.configuration.setdefault(key, self.default_configuration[key])
                missing_config.append(key)

        if missing_config:
            missing_keys = ', '.join([f'"{key}"' for key in missing_config])
            self._show_warning(f"发现缺失配置: \n{missing_keys} \n将使用默认配置！")

        # 比赛数据
        self.race_data = {
            "比赛进度": 0,
            "队伍名单": [
                {
                    "队伍编号": "Test",
                    "队伍名称": "Test",
                    "队伍成员": "Test",
                    "比赛阶段": "赛前准备阶段",
                    "剩余时间": self.configuration["赛前准备时间"],
                    "是否暂停": True,
                    "所有成绩": [
                        {
                            "原始时间": 20.744,
                            "修正时间": 20.744,
                            "状态": "未处理",
                            "罚时": [],
                        },
                        {
                            "原始时间": 24.552,
                            "修正时间": 24.552,
                            "状态": "未处理",
                            "罚时": [],
                        }
                    ],
                    "最好成绩": 999.999,
                }
            ],
        }

        # 倒计时
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        # 创建菜单栏
        menu_bar = self.menuBar()

        # 文件菜单
        file_menu = menu_bar.addMenu("文件")

        import_action = QAction("导入抽签结果", self)
        import_action.triggered.connect(self.import_team_list)
        file_menu.addAction(import_action)

        save_action = QAction("保存比赛结果", self)
        save_action.triggered.connect(self.save_team_list)
        file_menu.addAction(save_action)

        # 设置
        set_menu = menu_bar.addMenu("设置")

        communication_action = QAction("通信设置", self)
        communication_action.triggered.connect(lambda: self.open_dialog("通信设置"))
        set_menu.addAction(communication_action)

        race_action = QAction("比赛设置", self)
        race_action.triggered.connect(lambda: self.open_dialog("比赛设置"))
        set_menu.addAction(race_action)

        timing_action = QAction("计时设置", self)
        timing_action.triggered.connect(lambda: self.open_dialog("计时设置"))
        set_menu.addAction(timing_action)

        penalty_action = QAction("罚时设置", self)
        penalty_action.triggered.connect(lambda: self.open_dialog("罚时设置"))
        set_menu.addAction(penalty_action)

        screen_action = QAction("投屏设置", self)
        screen_action.triggered.connect(lambda: self.open_dialog("投屏设置"))
        set_menu.addAction(screen_action)

        # 投屏
        project_menu = menu_bar.addMenu("投屏")
        project_menu.aboutToShow.connect(self.update_project_menu)
        project_menu.setObjectName("投屏")
        self.screen_actions = {}

        # 关于
        about_action = menu_bar.addAction("关于")
        about_action.triggered.connect(self.show_about)

        # 创建状态栏
        self.status_bar = self.statusBar()

        # 主布局
        layout = QVBoxLayout()

        # 顶部标题
        font_title = QFont()
        font_title.setPointSize(14)
        self.race = create_label(font=font_title, style="margin-bottom: 5px;")
        layout.addWidget(self.race)

        # 展板布局
        display_layout = QGridLayout()

        progress = create_label("比赛进度")
        display_layout.addWidget(progress, 0, 0)

        team_id = create_label("队伍编号")
        display_layout.addWidget(team_id, 0, 1)

        team_name = create_label("队伍名称")
        display_layout.addWidget(team_name, 0, 2)

        team_members = create_label("队伍成员")
        display_layout.addWidget(team_members, 0, 3)
        layout.addLayout(display_layout)

        self.progress_display = create_label()
        display_layout.addWidget(self.progress_display, 1, 0)

        self.team_id_display = create_label()
        display_layout.addWidget(self.team_id_display, 1, 1)

        self.team_name_display = create_label()
        display_layout.addWidget(self.team_name_display, 1, 2)

        self.team_members_display = create_label()
        display_layout.addWidget(self.team_members_display, 1, 3)

        real_time = create_label("实时时间")
        display_layout.addWidget(real_time, 2, 0)

        self.race_phase_display = create_label()
        display_layout.addWidget(self.race_phase_display, 2, 1)

        self.real_time_display = create_label()
        time = f"{self.real_time:.3f}s"
        self.real_time_display.setText(time)
        display_layout.addWidget(self.real_time_display, 3, 0)

        self.remaining_time_display = create_label()
        display_layout.addWidget(self.remaining_time_display, 3, 1)

        self.start_and_pause_button = create_button("开始倒计时")
        self.start_and_pause_button.clicked.connect(self.toggle_start_and_pause_button)
        display_layout.addWidget(self.start_and_pause_button, 2, 2, 2, 1)

        self.modify_button = create_button("修改剩余时间")
        self.modify_button.clicked.connect(lambda: self.open_dialog("修改剩余时间"))
        display_layout.addWidget(self.modify_button, 2, 3, 2, 1)

        best_record = create_label("最好成绩")
        display_layout.addWidget(best_record, 4, 0)

        next_team = create_label("下支队伍")
        display_layout.addWidget(next_team, 4, 1)

        self.best_record_display = create_label()
        display_layout.addWidget(self.best_record_display, 5, 0)

        self.next_team_display = create_label()
        display_layout.addWidget(self.next_team_display, 5, 1)

        self.previous_team_button = create_button("切换上支队伍")
        self.previous_team_button.clicked.connect(self.switch_to_previous_team)
        display_layout.addWidget(self.previous_team_button, 4, 2, 2, 1)

        self.next_team_button = create_button("切换下支队伍")
        self.next_team_button.clicked.connect(self.switch_to_next_team)
        display_layout.addWidget(self.next_team_button, 4, 3, 2, 1)

        record_option = create_label("选择成绩")
        display_layout.addWidget(record_option, 6, 0)

        self.confirm_record_button = create_button("确认此次成绩")
        self.confirm_record_button.clicked.connect(lambda: self.update_record_state("已确认"))
        display_layout.addWidget(self.confirm_record_button, 6, 2, 2, 1)

        self.cancel_record_button = create_button("取消此次成绩")
        self.cancel_record_button.clicked.connect(lambda: self.update_record_state("已作废"))
        display_layout.addWidget(self.cancel_record_button, 6, 3, 2, 1)

        self.record_option_display = create_combo_box()
        display_layout.addWidget(self.record_option_display, 7, 0)

        self.add_record_button = create_button("添加比赛成绩")
        self.add_record_button.clicked.connect(lambda: self.open_dialog("添加比赛成绩"))
        display_layout.addWidget(self.add_record_button, 6, 1, 2, 1)

        # 已执行罚时
        left_widget = QWidget()
        left_scroll_area = QScrollArea()
        left_scroll_area.setWidget(left_widget)
        left_scroll_area.setWidgetResizable(True)
        display_layout.addWidget(left_scroll_area, 8, 0, 2, 3)
        self.left_layout = QFormLayout(left_widget)

        # 可选罚时
        right_widget = QWidget()
        right_scroll_area = QScrollArea()
        right_scroll_area.setWidget(right_widget)
        right_scroll_area.setWidgetResizable(True)
        display_layout.addWidget(right_scroll_area, 8, 3, 2, 1)
        self.right_layout = QVBoxLayout(right_widget)
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 设置列的伸展因子，控制左右区域的占比
        display_layout.setColumnStretch(0, 1)
        display_layout.setColumnStretch(1, 1)
        display_layout.setColumnStretch(2, 1)
        display_layout.setColumnStretch(3, 1)

        # 设置行的伸展因子
        display_layout.setRowStretch(8, 1)
        display_layout.setRowStretch(9, 1)

        layout.addLayout(display_layout)

        # 设置中心组件
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.update_title_settings()
        self.update_record_option()
        self.update_team_information()
        self.update_timer_display()
        self.update_penalty_panel()
        self.communication_thread["WS"] = WebSocketClientThread()
        self.communication_thread["WS"].start()

    def update_status(self, message):
        self.status_bar.showMessage(f"{datetime.datetime.now().strftime('%H:%M:%S')}: " + message, 0)

    def _show_warning(self, message):
        QMessageBox.warning(self, "警告", message)

    def update_full_screen_display(self, widget_name, text):
        if self.full_screen_window:
            widget = getattr(self.full_screen_window, widget_name, None)
            if widget and widget.text() != text:  # 仅在内容变化时才更新
                widget.setText(text)

    def import_team_list(self):
        if self.race_data["比赛进度"] > 0:
            self._show_warning("当前已开始比赛，请先清空队伍名单后再导入！")
            return

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "导入队伍名单",
            "",
            "Excel Files (*.xls *.xlsx);;CSV Files (*.csv);;All Files (*)"
        )

        if file_name:
            try:
                # 根据文件扩展名选择读取方法
                if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
                    df = pd.read_excel(file_name, header=None)
                elif file_name.endswith('.csv'):
                    # 检测文件编码
                    encoding = None
                    with open(file_name, 'rb') as f:
                        result = chardet.detect(f.read())
                        encoding = result['encoding']  # 读取编码

                    # 读取
                    try:
                        # 尝试用检测的文件编码读取
                        df = pd.read_csv(file_name, encoding=encoding, header=None)
                    except Exception:
                        # 使用检测的文件编码读取失败，尝试其他已知编码
                        alternative_encodings = ['utf-8', 'gbk', 'gb2312']
                        for alt_encoding in alternative_encodings:
                            try:
                                df = pd.read_csv(file_name, encoding=alt_encoding, header=None)
                                break
                            except Exception:
                                continue
                        if 'df' not in locals():
                            raise ValueError("无法使用任何编码读取文件。")
                else:
                    self._show_warning("不支持的文件格式！")
                    return

                team_list = []
                for index, row in df.iterrows():
                    team_members = [str(member) for member in row.iloc[2:6] if pd.notna(member)]  # 过滤掉第三至第六列的空值
                    team = {
                        "队伍编号": row.iloc[0],  # 第一列
                        "队伍名称": row.iloc[1],  # 第二列
                        "队伍成员": '、'.join(team_members),  # 把过滤结果合并为字符串
                        "比赛阶段": "赛前准备阶段",
                        "剩余时间": self.configuration["赛前准备时间"],
                        "是否暂停": True,
                        "所有成绩": [],
                        "最好成绩": 999.999,
                    }
                    team_list.append(team)

                self.race_data["队伍名单"] += team_list
                self.race_data["比赛进度"] = 1

                self.update_status(f"读取文件 {file_name} 成功！")
                self.update_team_information()
                self.update_timer_display()
                self.update_record_option()

            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取文件时出错：{e}")

    def save_team_list(self):
        if self.race_data["比赛进度"] == 0:
            self._show_warning("当前未开始比赛，无法保存比赛结果！")
            return

        # 打开文件选择对话框
        filename, _ = QFileDialog.getSaveFileName(None, "保存文件", "比赛结果", "Excel Files (*.xlsx);;All Files (*)")

        if filename:
            # 创建一个新的 Excel 工作簿
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "队伍信息"

            # 设置表头
            headers = ["队伍编号", "队伍名称", "最好成绩"]
            sheet.append(headers)

            # 添加字典信息到 Excel
            for team in self.race_data["队伍名单"][1:]:
                row_data = [
                    team["队伍编号"],
                    team["队伍名称"],
                    team["最好成绩"],
                ]
                sheet.append(row_data)

            # 保存
            workbook.save(filename)
            self.update_status(f"文件已保存到: {filename}")  # 可以根据需要打印或显示消息

    def open_dialog(self, dialog_type):
        dialog_map = {
            "通信设置": CommunicationSettingDialog(self.configuration, self.communication_thread),
            "比赛设置": CompetitionSettingDialog(self.configuration),
            "计时设置": TimerSettingDialog(self.configuration, self.race_data["比赛进度"]),
            "罚时设置": PenaltySettingDialog(self.configuration),
            "投屏设置": ScreenSettingDialog(self.configuration),
            "修改剩余时间": ModifyTimeDialog(self.race_data["队伍名单"][self.race_data["比赛进度"]]),
            "添加比赛成绩": AddRecordDialog(self.race_data["队伍名单"][self.race_data["比赛进度"]])
        }

        # 根据对话框类型创建对象
        if dialog_type in dialog_map:
            dialog = dialog_map[dialog_type]

            # 特定对话框需要连接信号
            if dialog_type == "通信设置":
                dialog.serial_port_state_changed.connect(self.open_serial_port)
                dialog.tcp_server_state_changed.connect(self.open_tcp_server)
                dialog.udp_server_state_changed.connect(self.open_udp_server)
                dialog.send_status.connect(self.update_status)
            elif dialog_type == "比赛设置":
                dialog.setting_saved.connect(self.update_title_settings)
            elif dialog_type == "罚时设置":
                dialog.setting_saved.connect(self.update_penalty_panel)
            elif dialog_type == "修改剩余时间":
                progress = self.race_data["比赛进度"]
                if self.race_data["队伍名单"][progress]["是否暂停"]:
                    dialog = ModifyTimeDialog(self.race_data["队伍名单"][progress])
                    dialog.setting_saved.connect(self.update_timer_display)
                else:
                    self._show_warning("请先暂停再修改剩余时间！")
                    return
            elif dialog_type == "添加比赛成绩":
                dialog.setting_saved.connect(self.update_record_option)
        else:
            return

        # 以模态方式显示对话框
        dialog.exec()

    def open_serial_port(self, config):
        self.communication_thread["串口"] = SerialPortThread(config[0], config[1])
        self.communication_thread["串口"].real_received.connect(self.update_real_time_display)
        self.communication_thread["串口"].final_received.connect(self.add_record)
        self.communication_thread["串口"].send_status.connect(self.update_status)
        self.communication_thread["串口"].timer_reset.connect(lambda: self.audio_play("重置"))
        self.communication_thread["串口"].start()

    def open_tcp_server(self, config):
        self.communication_thread["TCP"] = TcpServerThread(config[0], config[1])
        self.communication_thread["TCP"].real_received.connect(self.update_real_time_display)
        self.communication_thread["TCP"].final_received.connect(self.add_record)
        self.communication_thread["TCP"].send_status.connect(self.update_status)
        self.communication_thread["TCP"].timer_reset.connect(lambda: self.audio_play("重置"))
        self.communication_thread["TCP"].start()

    def open_udp_server(self, config):
        self.communication_thread["UDP"] = UdpServerThread(config[0], config[1])
        self.communication_thread["UDP"].real_received.connect(self.update_real_time_display)
        self.communication_thread["UDP"].final_received.connect(self.add_record)
        self.communication_thread["UDP"].send_status.connect(self.update_status)
        self.communication_thread["UDP"].timer_reset.connect(lambda: self.audio_play("重置"))
        self.communication_thread["UDP"].start()

    def update_title_settings(self):
        # 根据比赛组别设置对应的Key值（使用统一的映射关系）
        group_name = self.configuration["比赛组别"]
        if group_name in self.GROUP_KEY_MAPPING:
            self.configuration["Key"] = self.GROUP_KEY_MAPPING[group_name]
        self.race.setText(
            self.configuration["比赛名称"] + self.configuration["比赛阶段"] + self.configuration["比赛组别"])

        if self.full_screen_window:
            self.update_full_screen_display('title', self.configuration["比赛名称"] + self.configuration["比赛阶段"])
            self.update_full_screen_display('subheading', self.configuration["比赛组别"])

    def update_project_menu(self):
        project_menu = self.menuBar().findChild(QMenu, "投屏")

        if project_menu is None:
            return

        # 清空当前显示器
        project_menu.clear()

        # 获取当前所有显示器
        screens = QGuiApplication.screens()

        # 根据检测到的屏幕数量动态添加 QAction
        for i, screen in enumerate(screens):
            action = QAction(f"显示器 {i + 1}: {screen.name()}", self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, idx=i: self.project_to_screen(idx))
            project_menu.addAction(action)

    def project_to_screen(self, screen_index):
        if self.full_screen_window and self.full_screen_window.screen() == QApplication.screens()[screen_index]:
            self.full_screen_window.close()  # 关闭当前全屏窗口
            self.full_screen_window = None  # 清空当前全屏窗口
            return

        # 如果已经有全屏窗口打开，先关闭它
        if self.full_screen_window is not None:
            self.full_screen_window.close()

        # 创建全屏窗口
        self.full_screen_window = FullScreenWindow(self.configuration, self.race_data)
        screens = QApplication.screens()

        if 0 <= screen_index < len(screens):
            # 将全屏窗口移到指定的屏幕，始终全屏显示
            target_screen = screens[screen_index]
            screen_geometry = target_screen.geometry()
            self.full_screen_window.setGeometry(screen_geometry)
            self.full_screen_window.showFullScreen()

            # 信息更新
            self.update_team_information()
            self.update_timer_display()

    def show_about(self):
        QMessageBox.about(self, "关于","""
                                            <div style='text-align: center;'>
                                            <h2>北京科技大学智能汽车竞赛计时器</h2>
                                            <p>作者：谢翔远</p>
                                            <p>日期：2025年1月18日</p>
                                            <p>版本：V2.0</p>
                                            <p><i>轮到你，为世界加速！</i></p>
                                            """)

    def update_team_information(self):
        progress = self.race_data["比赛进度"]
        team_list = self.race_data["队伍名单"]
        team_data = team_list[progress]
        total_teams = len(team_list) - 1

        # 更新比赛进度
        self.progress_display.setText(f"{progress}/{total_teams}")

        # 更新全屏显示窗口
        if self.full_screen_window:
            self.update_full_screen_display("progress_display", f"{progress}/{total_teams}")

        # 更新队伍编号
        self.team_id_display.setText(team_data.get("队伍编号", "Null"))
        self.update_full_screen_display('team_id_display', team_data.get("队伍编号", "Null"))

        # 更新队伍名称
        self.team_name_display.setText(team_data.get("队伍名称", "Null"))
        self.update_full_screen_display('team_name_display', team_data.get("队伍名称", "Null"))

        # 更新队伍成员
        self.team_members_display.setText(team_data.get("队伍成员", "Null"))
        self.update_full_screen_display('team_members_display', team_data.get("队伍成员", "Null"))

        # 更新下一支队伍信息
        if progress + 1 < len(team_list):
            next_team = team_list[progress + 1]
            next_team_text = f"{next_team['队伍编号']}：{next_team['队伍名称']}"
        else:
            next_team_text = "无"

        self.next_team_display.setText(next_team_text)
        if self.full_screen_window:
            self.update_full_screen_display("next_team_display", next_team_text)

        # 更新计时器
        if progress > 0:
            self.update_timer_display()

        # 刷新大屏
        if self.full_screen_window:
            self.full_screen_window.update()

    def update_real_time_display(self, time):
        # 更新显示内容
        formatted_time = f"{time:.3f}s"
        self.real_time_display.setText(formatted_time)

        # 更新全屏窗口显示
        self.update_full_screen_display('real_time_display', formatted_time)

    def update_timer(self):
        progress = self.race_data["比赛进度"]
        team_data = self.race_data["队伍名单"][progress]

        # 如果比赛未暂停，进行时间更新
        if team_data["是否暂停"]:
            return

        # 减少剩余时间
        team_data["剩余时间"] -= 1

        if team_data["剩余时间"] <= 0:
            if team_data["比赛阶段"] == "赛前准备阶段":
                team_data["比赛阶段"] = "正式比赛阶段"
                team_data["剩余时间"] = self.configuration["比赛时间"]
            else:
                team_data["剩余时间"] = 0
                self.audio_play("时间到")
                self.toggle_start_and_pause_button()

        # 更新显示
        self.update_timer_display()

    def update_timer_display(self):
        progress = self.race_data["比赛进度"]

        # 比赛阶段
        race_stage = self.race_data["队伍名单"][progress].get("比赛阶段", "未知比赛阶段")
        self.race_phase_display.setText(race_stage)
        self.update_full_screen_display("race_phase_display", race_stage)

        # 剩余时间
        remaining_time = self.race_data["队伍名单"][progress].get("剩余时间", None)
        if remaining_time is not None:
            if remaining_time < 60:
                time_text = f'{remaining_time} 秒'
            else:
                minutes = remaining_time // 60
                seconds = remaining_time % 60
                time_text = f'{minutes} 分 {seconds} 秒'
            self.remaining_time_display.setText(time_text)
            self.update_full_screen_display("remaining_time_display", f'{time_text}')
            team_data = {
                **self.race_data["队伍名单"][progress],
                "Key": self.configuration["Key"]
            }
            json_str = json.dumps(team_data, ensure_ascii=False, indent=2)
            if self.communication_thread["WS"] != None:
                self.communication_thread["WS"].send_message(json_str)
        else:
            self.remaining_time_display.setText("Null")
            self.update_full_screen_display("remaining_time_display", "Null")

        # 最好成绩
        best_record = self.race_data["队伍名单"][progress].get("最好成绩", "Null")
        self.best_record_display.setText(f'{best_record}s')
        self.update_full_screen_display("best_record_display", f'{best_record}s')

        # 刷新大屏幕
        if self.full_screen_window:
            self.full_screen_window.update()

    def toggle_start_and_pause_button(self):
        progress = self.race_data["比赛进度"]
        team = self.race_data["队伍名单"][progress]

        # 切换暂停状态并更新按钮文本
        team["是否暂停"] = not team["是否暂停"]
        button_text = "开始倒计时" if team["是否暂停"] else "暂停倒计时"
        self.start_and_pause_button.setText(button_text)

    def modify_time(self):
        progress = self.race_data["比赛进度"]
        if not self.race_data["队伍名单"][progress]["是否暂停"]:
            self._show_warning("仅暂停状态下允许调整时间！")

    def switch_to_previous_team(self):
        progress = self.race_data["比赛进度"]

        # 检查是否有未处理成绩
        if self.check_unprocessed_scores(progress):
            return

        if progress == 0:
            self._show_warning("当前已经是第一支队伍！")
        else:
            self.switch_team(progress, -1)

    def switch_to_next_team(self):
        progress = self.race_data["比赛进度"]

        # 检查是否有未处理成绩
        if self.check_unprocessed_scores(progress):
            return

        if progress == len(self.race_data["队伍名单"]) - 1:
            self._show_warning("当前已经是最后一支队伍！")
        else:
            self.switch_team(progress, 1)

    def check_unprocessed_scores(self, progress):
        for data in self.race_data["队伍名单"][progress]["所有成绩"]:
            if data["状态"] == "未处理":
                self._show_warning("还有成绩未处理，请将所有成绩处理完毕后再切换队伍！")
                return True
        return False

    def switch_team(self, progress, step):
        if self.race_data["队伍名单"][progress]["是否暂停"]:
            self.race_data["比赛进度"] += step
            self.update_team_information()
            self.update_record_option()
            self.update_penalty_area()
        else:
            self._show_warning("请将比赛暂停后再调整比赛进度！")

    def update_record_option(self):
        progress = self.race_data["比赛进度"]
        all_records = self.race_data["队伍名单"][progress]["所有成绩"]

        # 获取当前选择的索引
        old_index = self.record_option_display.currentIndex() if self.record_option_display.currentText() else 0

        # 清除旧的显示内容
        self.record_option_display.clear()

        if all_records:
            # 遍历每个成绩
            for data in all_records:
                total_penalty = sum(penalty[1] for penalty in data['罚时'])
                self.record_option_display.addItem(f"{data['原始时间']:.3f}+{total_penalty} ({data['状态']})")

            # 设置默认选择项
            self.record_option_display.setCurrentIndex(old_index)

            # 获取所有项的索引并设置居中
            for i in range(self.record_option_display.count()):
                index = self.record_option_display.model().index(i, 0)
                self.record_option_display.model().setData(index,
                                                           Qt.AlignmentFlag.AlignCenter,
                                                           Qt.ItemDataRole.TextAlignmentRole)
        else:
            self.record_option_display.addItem("暂无成绩")
            index = self.record_option_display.model().index(0, 0)
            self.record_option_display.model().setData(index,
                                                       Qt.AlignmentFlag.AlignCenter,
                                                       Qt.ItemDataRole.TextAlignmentRole)

    def update_record_state(self, text):
        # 检查是否有选中的成绩
        if self.record_option_display.currentText() == "暂无成绩":
            self._show_warning("请先选中一个成绩再进行操作！")
            return

        progress = self.race_data["比赛进度"]
        index = self.record_option_display.currentIndex()

        # 更新选中成绩的状态
        team_data = self.race_data["队伍名单"][progress]
        team_data["所有成绩"][index]["状态"] = text

        # 更新显示
        self.update_record_option()

        # 更新最好成绩
        best_record = min((data["修正时间"] for data in team_data["所有成绩"] if data["状态"] == "已确认"), default=999.999)

        # 更新最好成绩显示
        team_data["最好成绩"] = best_record
        self.best_record_display.setText(f'{best_record:.3f}s')
        json_str = json.dumps(self.race_data["队伍名单"][progress], ensure_ascii=False, indent=2)
        if self.communication_thread["WS"] != None:
            self.communication_thread["WS"].send_message(json_str)

    def add_record(self, time):
        progress = self.race_data["比赛进度"]
        self.race_data["队伍名单"][progress]["所有成绩"].append({
            "原始时间": time,
            "修正时间": time,
            "状态": "未处理",
            "罚时": [],
        })

        self.update_record_option()
        self.update_status("成绩有更新，请及时处理！")

    def update_penalty_panel(self):
        # 清除右侧布局中的所有控件
        for i in reversed(range(self.right_layout.count())):
            item = self.right_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 遍历配置中的罚时种类
        penalty_types = self.configuration["罚时种类"]
        for text, value in penalty_types:
            button = QPushButton()

            # 预计算按钮文本
            if value >= 0:
                button_text = f"{text} (+{value}s)"
            else:
                button_text = f"{text} ({value}s)"

            button.setText(button_text)
            button.setStyleSheet("padding: 8px;")

            # 使用默认参数捕获当前的 text 和 value，避免闭包问题
            button.clicked.connect(lambda _, t=text, v=value: self.add_penalty((t, v)))

            # 将按钮添加到布局中
            self.right_layout.addWidget(button)

    def add_penalty(self, penalty):
        # 获取当前比赛进度和当前选中的成绩索引
        progress = self.race_data["比赛进度"]
        index = self.record_option_display.currentIndex()

        # 检查是否选中成绩
        if self.record_option_display.currentText() == "暂无成绩":
            self._show_warning("当前未选中任何成绩，不能添加罚时！")
            return

        # 检查选中成绩的状态是否已确认
        current_record = self.race_data["队伍名单"][progress]["所有成绩"][index]
        if current_record["状态"] == "已确认":
            self._show_warning("本次成绩已确认，不能添加罚时！")
            return

        # 添加罚时并进行时间计算
        current_record["罚时"].append(penalty)

        # 计算修正时间
        total_penalty = sum(penalty[1] for penalty in current_record["罚时"])
        corrected_time = current_record["原始时间"] + total_penalty

        # 更新修正时间
        current_record["修正时间"] = corrected_time

        # 更新界面
        self.update_record_option()
        self.update_penalty_area()

    def update_penalty_area(self):
        # 清除当前左侧布局中的所有控件
        for i in reversed(range(self.left_layout.count())):
            item = self.left_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 获取当前成绩的罚时列表
        progress = self.race_data["比赛进度"]
        try:
            penalties = self.race_data["队伍名单"][progress]["所有成绩"][self.record_option_display.currentIndex()]["罚时"]
        except Exception:
            return

        if penalties:
            grid_layout = QGridLayout()
            column_count = 4
            button_index = 0

            for text, value in penalties:
                button = QPushButton(f"{text} ({'+' if value >= 0 else ''}{value}s)")
                button.setStyleSheet("padding: 8px;")
                button.clicked.connect(lambda _, i=button_index: self.remove_penalty(penalties, i))

                # 计算行列位置
                row, col = divmod(button_index, column_count)
                grid_layout.addWidget(button, row, col)

                button_index += 1

            # 填充剩余的单元格（可选）
            if button_index % column_count != 0:
                row = button_index // column_count
                for empty_index in range(button_index % column_count, column_count):
                    grid_layout.addWidget(QWidget(), row, empty_index)  # 使用空QWidget作为占位符

            grid_widget = QWidget()
            grid_widget.setLayout(grid_layout)
            self.left_layout.addRow(grid_widget)

    def remove_penalty(self, penalties, penalty_index):
        progress = self.race_data["比赛进度"]
        record_index = self.record_option_display.currentIndex()

        # 确保成绩未确认才能修改罚时
        if self.race_data["队伍名单"][progress]["所有成绩"][record_index]["状态"] == "已确认":
            self._show_warning("本次成绩已确认，不能撤销罚时！")
            return

        # 确保索引有效
        if 0 <= penalty_index < len(penalties):
            # 删除指定罚时
            del penalties[penalty_index]
            self.update_record_option()
            self.update_penalty_area()

    def save_configuration(self):
        """保存配置到config.json文件"""
        # 根据比赛组别设置对应的Key值（使用统一的映射关系，确保保存时Key也是正确的）
        group_name = self.configuration["比赛组别"]
        if group_name in self.GROUP_KEY_MAPPING:
            self.configuration["Key"] = self.GROUP_KEY_MAPPING[group_name]

        # 保存到文件
        try:
            with open("config.json", "w", encoding="utf-8") as file:
                json.dump(self.configuration, file, ensure_ascii=False, indent=4)
        except Exception as e:
            self._show_warning(f"保存配置文件失败：{e}")

    def closeEvent(self, event):
        """窗口关闭事件，保存配置"""
        self.save_configuration()
        event.accept()

    def audio_play(self, type):
        path = self.audio_path[type]
        if not hasattr(self, 'task') or not self.task.isRunning():
            self.task = AudioPlayThread(path)
            self.task.start()
        if type == "重置":
            self.update_status("计时器已手动重置！")
            self.update_real_time_display(0)
        else:
            self.update_status("当前队伍比赛时间结束！")

    def get_group_filename(group_name):
        """
        根据比赛组别获取对应的文件名
        :param group_name: 比赛组别名称
        :return: 对应的文件名（不带扩展名）
        """
        group_mapping = {
            "摄像头组": "micro_electro",
            "电磁组": "electro_magnetic",
            "缩微光电组": "speed_electro"
        }

        # 如果组别在映射中，则返回对应的文件名，否则返回默认值
        return group_mapping.get(group_name, "micro_electro")


def search_file(filename, search_root=None):
    """
    从指定目录递归搜索文件.
    :param filename: 要搜索的文件名
    :param search_root: 起始搜索目录，默认为当前脚本目录
    :return: 文件的完整路径，若找不到返回 None
    """
    search_root = search_root or os.getcwd()
    for root, _, files in os.walk(search_root):
        if filename in files:
            return os.path.join(root, filename)
    return None
