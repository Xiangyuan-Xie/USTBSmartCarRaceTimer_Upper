"""Timer settings dialog window"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QPushButton, QSpinBox, QVBoxLayout

from widget.common import create_spin_box
from widget.dialog.base import BaseDialog, InfoDialog


class TimerSettingDialog(BaseDialog):
    def __init__(self, configuration, progress):
        super().__init__()
        self.setWindowTitle("计时设置")
        self.configuration = configuration
        self.progress = progress

        layout = QVBoxLayout()

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(15)

        # Speed calculation
        self.set_speed_calculation = QCheckBox("启用速度计算")
        self.set_speed_calculation.setChecked(self.configuration["速度计算"])
        self.set_speed_calculation.setStyleSheet("""
            QCheckBox { font-family: "Microsoft YaHei"; font-size: 14px; color: #606266; }
            QCheckBox::indicator { width: 18px; height: 18px; }
        """)
        layout.addWidget(self.set_speed_calculation)

        # Track length
        self.set_length = create_spin_box(
            QDoubleSpinBox,
            min_value=0,
            current_value=self.configuration["赛道长度"],
            single_step=0.1,
            decimals=1,
            suffix=" 米",
        )
        form_layout.addRow("赛道长度:", self.set_length)

        # Preparation time
        self.set_preparation_time = create_spin_box(
            QSpinBox, min_value=0, max_value=65535, current_value=self.configuration["赛前准备时间"], suffix=" 秒"
        )
        form_layout.addRow("赛前准备时间:", self.set_preparation_time)

        # Competition time
        self.set_competition_time = create_spin_box(
            QSpinBox, min_value=0, max_value=65535, current_value=self.configuration["比赛时间"], suffix=" 秒"
        )
        form_layout.addRow("比赛时间:", self.set_competition_time)

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
        """)
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
        if self.progress > 0:
            InfoDialog("警告", "当前比赛已开始，不能再修改计时设置！", self).exec()
        else:
            self.configuration["速度计算"] = self.set_speed_calculation.isChecked()
            self.configuration["赛道长度"] = self.set_length.value()
            self.configuration["赛前准备时间"] = self.set_preparation_time.value()
            self.configuration["比赛时间"] = self.set_competition_time.value()
            self.accept()  # Close dialog
