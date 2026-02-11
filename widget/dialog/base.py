from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class BaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Ensure we have a close button but no context help button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: "Microsoft YaHei";
                font-size: 14px;
            }
            QLabel {
                font-family: "Microsoft YaHei";
                font-size: 14px;
                color: #303133;
                font-weight: bold;
                background-color: transparent;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 6px;
                font-family: "Microsoft YaHei";
                font-size: 14px;
                color: #606266;
                background-color: #ffffff;
                min-height: 20px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #409eff;
            }
            QPushButton, QToolButton {
                background-color: #ffffff;
                border: 1px solid #dcdfe6;
                color: #606266;
                border-radius: 4px;
                padding: 6px 15px;
                font-family: "Microsoft YaHei";
                font-size: 14px;
            }
            QToolButton {
                padding: 2px;
            }
            QPushButton:hover, QToolButton:hover {
                color: #409eff;
                border-color: #c6e2ff;
                background-color: #ecf5ff;
            }
            QPushButton:pressed, QToolButton:pressed {
                color: #3a8ee6;
                border-color: #3a8ee6;
            }
            /* ScrollBar Styling */
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def set_content_layout(self, layout):
        """Helper to set the main layout with standard margins"""
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)


class InfoDialog(BaseDialog):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout()

        label = QLabel(content)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        label.setTextFormat(Qt.RichText)
        label.setOpenExternalLinks(True)
        layout.addWidget(label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("确定")
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                border: 1px solid #409eff;
                color: #ffffff;
                padding: 6px 20px;
            }
            QPushButton:hover {
                background-color: #66b1ff;
                border-color: #66b1ff;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()

        layout.addSpacing(10)
        layout.addLayout(btn_layout)

        self.set_content_layout(layout)

        # Adjust size based on content, but set a min width
        self.setMinimumWidth(350)
