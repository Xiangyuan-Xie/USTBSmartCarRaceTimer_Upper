from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout

from .common import *


class FullScreenWindow(QWidget):
    def __init__(self, configuration, race_data):
        super().__init__()
        self.configuration = configuration
        self.race_data = race_data
        self.initialization = False
        self.setWindowTitle("投屏窗口")

        self.setStyleSheet("""
            QWidget {
                background-color: black;
                color: white;
            }
            QLabel {
                background-color: black;
                color: white;
            } 
        """)

        # 获取缩放比例（用于调整字体大小，窗口保持全屏）
        self.scale_factor = self.configuration.get("投屏缩放比例", 1.0)

        # 创建主布局
        layout = QVBoxLayout()
        # 布局间距也根据缩放比例调整
        layout.setSpacing(int(10 * self.scale_factor))
        layout.setContentsMargins(
            int(20 * self.scale_factor),
            int(20 * self.scale_factor),
            int(20 * self.scale_factor),
            int(20 * self.scale_factor)
        )

        # 设置初始字体大小
        self.fontTitle = QFont()
        self.font = QFont()
        # 标题字体也稍微受缩放影响，但影响较小
        base_title_size = 15
        self.fontTitle.setPointSize(int(base_title_size * min(1.0, self.scale_factor * 1.2)))
        # 内容字体根据缩放比例调整
        base_font_size = 30
        self.font.setPointSize(int(base_font_size * self.scale_factor))

        # 标题（间距也根据缩放比例调整）
        title_margin_top = int(30 * self.scale_factor)
        title_margin_bottom = int(10 * self.scale_factor)
        self.title = create_label(
            self.configuration["比赛名称"] + self.configuration["比赛阶段"], 
            font=self.fontTitle,
            style=f"color: #FFD700; font: bold; margin-top: {title_margin_top}px; margin-bottom: {title_margin_bottom}px;"
        )
        layout.addWidget(self.title)

        subheading_margin_top = int(10 * self.scale_factor)
        subheading_margin_bottom = int(20 * self.scale_factor)
        self.subheading = create_label(
            self.configuration["比赛组别"], 
            font=self.fontTitle,
            style=f"color: #FFD700; font: bold; margin-top: {subheading_margin_top}px; margin-bottom: {subheading_margin_bottom}px;"
        )
        layout.addWidget(self.subheading)

        # 比赛信息
        grid_layout = QGridLayout()
        # 网格布局的间距也根据缩放比例调整
        grid_layout.setSpacing(int(10 * self.scale_factor))

        # 保存所有静态标签的引用，以便后续更新字体
        self.static_labels = []
        
        progress = create_label("比赛进度", font=self.font)
        grid_layout.addWidget(progress, 0, 0)
        self.static_labels.append(progress)

        self.progress_display = create_label(font=self.font, style="color: #FFA500;")
        grid_layout.addWidget(self.progress_display, 0, 1)

        next_team = create_label("下支队伍", font=self.font)
        grid_layout.addWidget(next_team, 0, 2)
        self.static_labels.append(next_team)

        self.next_team_display = create_label(font=self.font, style="color: #FFA500;")
        grid_layout.addWidget(self.next_team_display, 0, 3)

        team_id = create_label("队伍号", font=self.font)
        grid_layout.addWidget(team_id, 1, 0)
        self.static_labels.append(team_id)

        self.team_id_display = create_label(font=self.font, style="color: #FFA500;")
        grid_layout.addWidget(self.team_id_display, 1, 1)

        real_time = create_label("实时时间", font=self.font)
        grid_layout.addWidget(real_time, 1, 2)
        self.static_labels.append(real_time)

        self.real_time_display = create_label(font=self.font)
        grid_layout.addWidget(self.real_time_display, 1, 3)

        team_name = create_label("队伍名称", font=self.font)
        grid_layout.addWidget(team_name, 2, 0)
        self.static_labels.append(team_name)

        self.team_name_display = create_label(font=self.font, style="color: #FFA500;")
        grid_layout.addWidget(self.team_name_display, 2, 1)

        best_record = create_label("最好成绩", font=self.font)
        grid_layout.addWidget(best_record, 2, 2)
        self.static_labels.append(best_record)

        self.best_record_display = create_label(font=self.font, style="color: #FF0000;")
        grid_layout.addWidget(self.best_record_display, 2, 3)

        team_members = create_label("队伍成员", font=self.font)
        grid_layout.addWidget(team_members, 3, 0)
        self.static_labels.append(team_members)

        self.team_members_display = create_label(font=self.font, style="color: #FFA500;")
        grid_layout.addWidget(self.team_members_display, 3, 1)

        remaining_time = create_label("剩余时间", font=self.font)
        grid_layout.addWidget(remaining_time, 3, 2)
        self.static_labels.append(remaining_time)

        self.remaining_time_display = create_label(font=self.font)
        grid_layout.addWidget(self.remaining_time_display, 3, 3)

        # 设置行高均匀分布
        column_count = grid_layout.columnCount()
        for i in range(column_count):
            grid_layout.setRowStretch(i, 1)

        layout.addLayout(grid_layout)

        # 提示（间距也根据缩放比例调整）
        attention_margin_top = int(30 * self.scale_factor)
        attention_margin_bottom = int(30 * self.scale_factor)
        self.attention = create_label(
            ">>>>>>>>>>  北科大智能车队提醒您，冷静发车，赛出实力！ <<<<<<<<<<", 
            font=self.font,
            style=f"color: #FFFF00; font: bold; margin-top: {attention_margin_top}px; margin-bottom: {attention_margin_bottom}px;"
        )
        layout.addWidget(self.attention)

        self.setLayout(layout)
        self.initialization = True

    def resizeEvent(self, event):
        # 根据窗口大小动态调整字体大小，确保在不同分辨率下都能正常显示
        width = self.width()
        height = self.height()
        # 使用较小的维度来计算字体大小，确保内容不会被裁剪
        min_dimension = min(width, height)
        base_font_size = max(10, min_dimension // 40)
        # 应用缩放比例
        new_font_size = int(base_font_size * self.scale_factor)
        self.font.setPointSize(new_font_size)
        # 标题字体也稍微受缩放影响，但影响较小
        base_title_size = max(8, base_font_size // 2)
        self.fontTitle.setPointSize(int(base_title_size * min(1.0, self.scale_factor * 1.2)))
        self.title.setFont(self.fontTitle)
        self.subheading.setFont(self.fontTitle)
        
        # 更新所有使用内容字体的控件（排除标题）
        # 更新静态标签
        for label in self.static_labels:
            if label:
                label.setFont(self.font)
        # 更新显示控件
        widgets_to_update = [
            self.progress_display, self.next_team_display,
            self.team_id_display, self.real_time_display,
            self.team_name_display, self.best_record_display,
            self.team_members_display, self.remaining_time_display,
            self.attention
        ]
        for widget in widgets_to_update:
            if widget:
                widget.setFont(self.font)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
