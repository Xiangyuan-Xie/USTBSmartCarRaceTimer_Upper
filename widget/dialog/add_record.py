""" 手动添加成绩对话窗口 """

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QDialog, QFormLayout

from widget.common import *


class AddRecordDialog(QDialog):
    setting_saved = Signal()

    def __init__(self, team):
        super().__init__()
        self.setWindowTitle("添加比赛成绩")
        self.team = team

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignCenter)

        # 成绩1
        self.add_record1 = create_spin_box(QDoubleSpinBox, min_value=0, max_value=999, current_value=0, decimals=3, suffix=" 秒")
        form_layout.addRow(QLabel("比赛成绩1:"), self.add_record1)

        # 成绩2
        self.add_record2 = create_spin_box(QDoubleSpinBox, min_value=0, max_value=999, current_value=0, decimals=3, suffix=" 秒")
        form_layout.addRow(QLabel("比赛成绩2:"), self.add_record2)

        # 成绩3
        self.add_record3 = create_spin_box(QDoubleSpinBox, min_value=0, max_value=999, current_value=0, decimals=3, suffix=" 秒")
        form_layout.addRow(QLabel("比赛成绩3:"), self.add_record3)

        # 保存和取消按钮
        self.submit_button = create_button("保存", style="")
        self.submit_button.clicked.connect(self.save_data)
        self.cancel_button = create_button("取消", style="")
        self.cancel_button.clicked.connect(self.close)
        form_layout.addRow(self.submit_button, self.cancel_button)

        layout.addLayout(form_layout)
        self.setLayout(layout)

    def save_data(self):
        valid_record = 0
        total_record = 0

        if self.add_record1.value() > 0:
            valid_record += 1
            total_record += self.add_record1.value()
        if self.add_record2.value() > 0:
            valid_record += 1
            total_record += self.add_record2.value()
        if self.add_record3.value() > 0:
            valid_record += 1
            total_record += self.add_record3.value()

        if valid_record > 0:
            average_record = total_record / valid_record
        else:
            average_record = 999.999

        self.team["所有成绩"].append({
            "原始时间": average_record,
            "修正时间": average_record,
            "状态": "未处理",
            "罚时": [],
        })
        self.setting_saved.emit()
        self.accept()
