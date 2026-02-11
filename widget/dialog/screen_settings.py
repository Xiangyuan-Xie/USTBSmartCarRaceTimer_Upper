""" 投屏设置对话窗口 """

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QDialog, QFormLayout, QLabel, QDoubleSpinBox, QPushButton

from widget.common import *


class ScreenSettingDialog(QDialog):
    setting_saved = Signal()

    def __init__(self, configuration):
        super().__init__()
        self.setWindowTitle("投屏设置")
        self.configuration = configuration

        layout = QVBoxLayout()

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignCenter)

        # 分辨率缩放比例
        # 默认值为1.0（100%），范围0.5-2.0（50%-200%）
        scale_factor = self.configuration.get("投屏缩放比例", 1.0)
        self.set_scale = QDoubleSpinBox()
        self.set_scale.setMinimum(0.5)
        self.set_scale.setMaximum(2.0)
        self.set_scale.setSingleStep(0.1)
        self.set_scale.setDecimals(2)
        self.set_scale.setValue(scale_factor)
        self.set_scale.setSuffix("x")
        form_layout.addRow(QLabel("分辨率缩放比例:"), self.set_scale)

        # 说明文字
        hint_label = QLabel("提示：如果投屏显示不完全，可以调整缩放比例。\n"
                           "小于1.0会缩小显示，大于1.0会放大显示。\n"
                           "建议范围：0.8 - 1.2")
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: gray; font-size: 10pt;")
        form_layout.addRow("", hint_label)

        # 保存与取消按钮
        self.submit_button = QPushButton("保存", self)
        self.submit_button.clicked.connect(self.save_data)
        self.cancel_button = QPushButton("取消", self)
        self.cancel_button.clicked.connect(self.close)
        form_layout.addRow(self.submit_button, self.cancel_button)

        layout.addLayout(form_layout)
        self.setLayout(layout)

    def save_data(self):
        self.configuration["投屏缩放比例"] = self.set_scale.value()
        self.setting_saved.emit()
        self.accept()

