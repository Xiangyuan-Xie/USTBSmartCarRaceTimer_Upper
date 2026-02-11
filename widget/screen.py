from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from .common import create_label


class FullScreenWindow(QWidget):
    def __init__(self, configuration, race_data):
        super().__init__()
        self.configuration = configuration
        self.race_data = race_data
        self.initialization = False
        self.setWindowTitle("投屏窗口")

        self.setStyleSheet("""
            QWidget {
                background-color: #0a0a0a;
                color: #ffffff;
            }
            QLabel {
                background-color: transparent;
                color: #ffffff;
            }
            #title_label {
                color: #ffd700;
                font-weight: bold;
            }
            #subheading_label {
                color: #ffd700;
                font-weight: bold;
            }
            #header_text {
                color: #909399;
                font-weight: normal;
            }
            #value_text {
                color: #ffa500;
                font-weight: bold;
            }
            #time_value {
                color: #409eff;
                font-weight: bold;
            }
            #remaining_value {
                color: #f56c6c;
                font-weight: bold;
            }
            #best_value {
                color: #67c23a;
                font-weight: bold;
            }
            #attention_label {
                color: #ffd700;
                font-weight: bold;
                background-color: #1a1a1a;
                padding: 10px;
                border-radius: 5px;
            }
        """)

        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)

        # 1. Header (Title & Subtitle)
        header_layout = QVBoxLayout()
        self.title = create_label(self.configuration["比赛名称"] + self.configuration["比赛阶段"])
        self.title.setObjectName("title_label")
        self.subheading = create_label(self.configuration["比赛组别"])
        self.subheading.setObjectName("subheading_label")
        header_layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.subheading, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(header_layout)

        self.main_layout.addStretch(1)

        # 2. Main Content Grid
        grid_container = QWidget()
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(40)  # Increased spacing
        self.grid_layout.setContentsMargins(40, 20, 40, 20)  # Added padding

        # Helper to add grid item (Label + Value stacked)
        def add_grid_item(label_widget, value_widget, row, col):
            container = QWidget()
            container.setStyleSheet(
                "background-color: rgba(255, 255, 255, 0.05); border-radius: 12px;"
            )  # Slightly lighter and more rounded
            layout = QVBoxLayout(container)
            layout.setContentsMargins(20, 20, 20, 20)  # More internal padding
            layout.addWidget(label_widget, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(value_widget, alignment=Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(container, row, col)

        # Make columns stretch equally
        for i in range(4):
            self.grid_layout.setColumnStretch(i, 1)
        # Make rows stretch equally
        for i in range(2):
            self.grid_layout.setRowStretch(i, 1)

        # Row 1: Team Info
        self.lbl_progress = create_label("比赛进度")
        self.lbl_progress.setObjectName("header_text")
        self.progress_display = create_label("0/0")
        self.progress_display.setObjectName("value_text")
        add_grid_item(self.lbl_progress, self.progress_display, 0, 0)

        self.lbl_team_id = create_label("队伍号")
        self.lbl_team_id.setObjectName("header_text")
        self.team_id_display = create_label("---")
        self.team_id_display.setObjectName("value_text")
        add_grid_item(self.lbl_team_id, self.team_id_display, 0, 1)

        self.lbl_team_name = create_label("队伍名称")
        self.lbl_team_name.setObjectName("header_text")
        self.team_name_display = create_label("等待导入")
        self.team_name_display.setObjectName("value_text")
        add_grid_item(self.lbl_team_name, self.team_name_display, 0, 2)

        self.lbl_team_members = create_label("队伍成员")
        self.lbl_team_members.setObjectName("header_text")
        self.team_members_display = create_label("---")
        self.team_members_display.setObjectName("value_text")
        add_grid_item(self.lbl_team_members, self.team_members_display, 0, 3)

        # Row 2: Timing & Status
        self.lbl_phase = create_label("当前阶段")
        self.lbl_phase.setObjectName("header_text")
        self.race_phase_display = create_label("赛前准备")
        self.race_phase_display.setObjectName("value_text")
        add_grid_item(self.lbl_phase, self.race_phase_display, 1, 0)

        self.lbl_real_time = create_label("实时时间")
        self.lbl_real_time.setObjectName("header_text")
        self.real_time_display = create_label("0.000s")
        self.real_time_display.setObjectName("time_value")
        add_grid_item(self.lbl_real_time, self.real_time_display, 1, 1)

        self.lbl_remaining_time = create_label("剩余时间")
        self.lbl_remaining_time.setObjectName("header_text")
        self.remaining_time_display = create_label("00:00")
        self.remaining_time_display.setObjectName("remaining_value")
        add_grid_item(self.lbl_remaining_time, self.remaining_time_display, 1, 2)

        self.lbl_best_record = create_label("最好成绩")
        self.lbl_best_record.setObjectName("header_text")
        self.best_record_display = create_label("999.999s")
        self.best_record_display.setObjectName("best_value")
        add_grid_item(self.lbl_best_record, self.best_record_display, 1, 3)

        self.main_layout.addWidget(grid_container)

        self.main_layout.addStretch(1)

        # 3. Footer (Next Team & Attention)
        footer_layout = QVBoxLayout()

        next_team_container = QHBoxLayout()
        self.lbl_next_team = create_label("下支队伍: ")
        self.lbl_next_team.setObjectName("header_text")
        self.next_team_display = create_label("---")
        self.next_team_display.setObjectName("value_text")
        next_team_container.addStretch()
        next_team_container.addWidget(self.lbl_next_team)
        next_team_container.addWidget(self.next_team_display)
        next_team_container.addStretch()

        self.attention = create_label(">>>>>>>>>>  北科大智能车队提醒您，冷静发车，赛出实力！ <<<<<<<<<<")
        self.attention.setObjectName("attention_label")

        footer_layout.addLayout(next_team_container)
        footer_layout.addSpacing(20)
        footer_layout.addWidget(self.attention, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(footer_layout)

        self.initialization = True
        self._update_fonts()

    def _update_fonts(self):
        w = self.width()
        h = self.height()

        # Scale factor based on diagonal or min dimension
        base_size = min(w, h)

        title_font = QFont("Microsoft YaHei", int(base_size // 25), QFont.Weight.Bold)
        sub_font = QFont("Microsoft YaHei", int(base_size // 35), QFont.Weight.Bold)
        header_font = QFont("Microsoft YaHei", int(base_size // 45))
        value_font = QFont("Microsoft YaHei", int(base_size // 35), QFont.Weight.Bold)
        big_value_font = QFont("Microsoft YaHei", int(base_size // 25), QFont.Weight.Bold)
        footer_font = QFont("Microsoft YaHei", int(base_size // 55), QFont.Weight.Bold)

        self.title.setFont(title_font)
        self.subheading.setFont(sub_font)

        # Grid labels
        for lbl in [
            self.lbl_progress,
            self.lbl_team_id,
            self.lbl_team_name,
            self.lbl_team_members,
            self.lbl_phase,
            self.lbl_real_time,
            self.lbl_remaining_time,
            self.lbl_best_record,
            self.lbl_next_team,
        ]:
            lbl.setFont(header_font)

        for val in [
            self.progress_display,
            self.team_id_display,
            self.team_name_display,
            self.team_members_display,
            self.race_phase_display,
            self.next_team_display,
        ]:
            val.setFont(value_font)

        for big_val in [self.real_time_display, self.remaining_time_display, self.best_record_display]:
            big_val.setFont(big_value_font)

        self.attention.setFont(footer_font)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.initialization:
            self._update_fonts()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
