"""罚时设置对话窗口"""

from copy import deepcopy

import pandas as pd
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from widget.common import create_label, create_line_edit, create_spin_box
from widget.dialog.base import BaseDialog


class PenaltySettingDialog(BaseDialog):
    setting_saved = Signal()

    def __init__(self, configuration):
        super().__init__()
        self.setWindowTitle("罚时设置")
        self.resize(550, 600)
        self.configuration = configuration
        self.penalties = deepcopy(configuration["罚时种类"])

        # 创建布局
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 导入按钮
        self.import_button = QPushButton("从 Excel 导入罚时种类")
        self.import_button.setCursor(Qt.PointingHandCursor)
        self.import_button.clicked.connect(self.import_penalties)
        layout.addWidget(self.import_button)

        # 滚动区域
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: 1px solid #dcdfe6; border-radius: 4px; background-color: #ffffff; }
        """)
        layout.addWidget(self.scroll_area)

        # 显示区域
        penalty_widget = QWidget()
        penalty_widget.setStyleSheet("background-color: #ffffff;")
        self.penalty_layout = QGridLayout(penalty_widget)
        self.penalty_layout.setSpacing(10)
        # Set column stretch
        self.penalty_layout.setColumnStretch(0, 3)  # Name
        self.penalty_layout.setColumnStretch(1, 2)  # Duration
        self.penalty_layout.setColumnStretch(2, 1)  # Button

        self.scroll_area.setWidget(penalty_widget)

        # 添加保存和取消按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

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

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.submit_button)

        layout.addLayout(button_layout)

        self.set_content_layout(layout)

        self.update_penalty_list()

    def import_penalties(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "导入罚时种类", "", "Excel Files (*.xls *.xlsx);;All Files (*)"
        )

        if file_name:
            try:
                df = pd.read_excel(file_name)

                penalties_list = []  # 读入的罚时种类
                invalid_rows = []  # 用于记录无效行的索引

                for index, row in df.iterrows():
                    penalty_type = row[0]  # 第一列
                    penalty_duration = row[1]  # 第二列

                    # 类型检查
                    if isinstance(penalty_type, str) and isinstance(penalty_duration, (int, float)):
                        penalties_list.append((penalty_type, int(penalty_duration)))  # 将有效元组添加到列表中
                    else:
                        invalid_rows.append(index + 1)  # 记录无效行的行号（+1 以符合 Excel 行号）

                # 合并罚时种类
                for new_penalty, new_duration in penalties_list:
                    found = False
                    for index, (penalty, duration) in enumerate(self.penalties):
                        if new_penalty == penalty:
                            self.penalties[index] = (penalty, new_duration)
                            found = True
                            break
                    if not found:
                        self.penalties.append((new_penalty, new_duration))

                # 存在无效行
                if invalid_rows:
                    invalid_rows_str = ", ".join(map(str, invalid_rows))
                    QMessageBox.warning(self, "警告", f"以下行的数据不符合格式：{invalid_rows_str}。请检查并重新导入。")

                self.update_penalty_list()

            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取文件时出错：{e}")

    def update_penalty_list(self):
        # 清除罚时面板中的所有控件
        while self.penalty_layout.count():
            item = self.penalty_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.penalties:
            spacer_top = QSpacerItem(0, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.penalty_layout.addItem(spacer_top, 0, 0, 1, 3)

            empty_label = create_label("罚时种类为空，请手动导入或添加！")
            empty_label.setStyleSheet("font-size: 14px; color: #909399;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.penalty_layout.addWidget(empty_label, 1, 0, 1, 3)

            # Still show add row at bottom if empty? Yes.
            row_offset = 2
        else:
            # Headers
            type_label = create_label("罚时种类")
            self.penalty_layout.addWidget(type_label, 0, 0)

            duration_label = create_label("时长")
            self.penalty_layout.addWidget(duration_label, 0, 1)

            op_label = create_label("操作")
            self.penalty_layout.addWidget(op_label, 0, 2)

            # Divider
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet("background-color: #dcdfe6; margin-bottom: 5px;")
            self.penalty_layout.addWidget(line, 1, 0, 1, 3)

            button_size = QSize(24, 24)
            row_offset = 2

            for number, (penalty_type, penalty_duration) in enumerate(self.penalties):
                curr_row = number + row_offset

                set_type = create_line_edit(text=penalty_type, alignment=Qt.AlignmentFlag.AlignLeft)
                set_type.editingFinished.connect(
                    lambda line_edit=set_type, n=number: self.update_penalty_text(n, line_edit)
                )
                self.penalty_layout.addWidget(set_type, curr_row, 0)

                set_duration = create_spin_box(
                    QSpinBox,
                    min_value=-32768,
                    max_value=32767,
                    current_value=penalty_duration,
                    suffix=" 秒",
                    alignment=Qt.AlignmentFlag.AlignCenter,
                )
                set_duration.editingFinished.connect(
                    lambda spinbox=set_duration, n=number: self.update_penalty_duration(n, spinbox)
                )
                self.penalty_layout.addWidget(set_duration, curr_row, 1)

                remove_button = QToolButton()
                remove_button.setText("×")
                remove_button.setFixedSize(button_size)
                remove_button.setCursor(Qt.PointingHandCursor)
                remove_button.setStyleSheet("""
                    QToolButton {
                        color: #f56c6c;
                        border: 1px solid #fbc4c4;
                        background-color: #fef0f0;
                        border-radius: 4px;
                    }
                    QToolButton:hover { background-color: #fde2e2; }
                """)
                remove_button.clicked.connect(lambda _, n=number: self.remove_penalty(n))
                self.penalty_layout.addWidget(remove_button, curr_row, 2, alignment=Qt.AlignCenter)

            row_offset += len(self.penalties)

        # Add New Row
        # Divider
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        line2.setStyleSheet("background-color: #dcdfe6; margin-top: 10px; margin-bottom: 5px;")
        self.penalty_layout.addWidget(line2, row_offset, 0, 1, 3)
        row_offset += 1

        add_type = create_line_edit(placeholder="新罚时名称", alignment=Qt.AlignmentFlag.AlignLeft)
        self.penalty_layout.addWidget(add_type, row_offset, 0)

        add_duration = create_spin_box(
            QSpinBox, min_value=-32768, max_value=32767, suffix=" 秒", alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.penalty_layout.addWidget(add_duration, row_offset, 1)

        add_button = QToolButton()
        add_button.setText("+")
        add_button.setFixedSize(QSize(24, 24))
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.setStyleSheet("""
            QToolButton { color: #67c23a; border: 1px solid #c2e7b0; background-color: #f0f9eb; border-radius: 4px; }
            QToolButton:hover { background-color: #e1f3d8; }
        """)
        add_button.clicked.connect(lambda: self.add_penalty(add_type.text(), add_duration.value()))
        self.penalty_layout.addWidget(add_button, row_offset, 2, alignment=Qt.AlignCenter)

        # Spacer at bottom
        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.penalty_layout.addItem(spacer, row_offset + 1, 0, 1, 3)

    def remove_penalty(self, index):
        if 0 <= index < len(self.penalties):
            del self.penalties[index]
            self.update_penalty_list()

    def add_penalty(self, penalty_type, penalty_duration):
        if penalty_type:
            self.penalties.append((penalty_type, penalty_duration))
            self.update_penalty_list()
        else:
            QMessageBox.warning(self, "提示", "请输入罚时种类名称！")

    def update_penalty_text(self, index, line_edit):
        if 0 <= index < len(self.penalties):
            self.penalties[index] = (line_edit.text(), self.penalties[index][1])

    def update_penalty_duration(self, index, spinbox):
        if 0 <= index < len(self.penalties):
            self.penalties[index] = (self.penalties[index][0], spinbox.value())

    def save_data(self):
        self.configuration["罚时种类"] = self.penalties
        self.setting_saved.emit()
        self.close()
