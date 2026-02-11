"""比赛设置对话窗口"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QPushButton, QVBoxLayout, QLabel

from widget.common import create_line_edit, create_combo_box
from widget.dialog.base import BaseDialog


class CompetitionSettingDialog(BaseDialog):
    setting_saved = Signal()

    def __init__(self, configuration):
        super().__init__()
        self.setWindowTitle("比赛设置")
        self.configuration = configuration

        # 预定义组别选项
        self.category_options = ["摄像头组", "电磁组", "缩微光电组"]

        layout = QVBoxLayout()

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)  # Right align labels usually looks better
        form_layout.setSpacing(15)

        # 比赛名称
        self.set_title = create_line_edit(self.configuration["比赛名称"])
        form_layout.addRow("比赛名称:", self.set_title)

        # 比赛阶段
        self.set_stage = create_line_edit(self.configuration["比赛阶段"])
        form_layout.addRow("比赛阶段:", self.set_stage)

        # 比赛组别 - 使用下拉选择框
        self.set_category = create_combo_box()
        self.set_category.addItems(self.category_options)

        # 设置当前选中的组别
        current_category = self.configuration["比赛组别"]
        if current_category in self.category_options:
            self.set_category.setCurrentText(current_category)
        else:
            self.set_category.setCurrentText(self.category_options[0])  # 默认选择第一个

        form_layout.addRow(QLabel("比赛组别:"), self.set_category)

        layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.submit_button = QPushButton("保存", self)
        self.submit_button.setCursor(Qt.PointingHandCursor)
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                border: 1px solid #409eff;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #66b1ff;
                border-color: #66b1ff;
            }
        """)  # Primary button style
        self.submit_button.clicked.connect(self.save_data)

        self.cancel_button = QPushButton("取消", self)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self.close)

        btn_layout.addWidget(self.cancel_button)
        btn_layout.addWidget(self.submit_button)

        layout.addSpacing(10)
        layout.addLayout(btn_layout)

        self.set_content_layout(layout)

    def save_data(self):
        self.configuration["比赛名称"] = self.set_title.text()
        self.configuration["比赛阶段"] = self.set_stage.text()
        self.configuration["比赛组别"] = self.set_category.currentText()  # 获取选择的文本
        self.setting_saved.emit()
        self.accept()