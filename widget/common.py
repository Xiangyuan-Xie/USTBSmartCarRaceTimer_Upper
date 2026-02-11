from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QDoubleSpinBox, QLineEdit, QComboBox


def create_label(text="", alignment=Qt.AlignmentFlag.AlignCenter, font=None, style=None):
    """
    创建并返回配置好的 QLabel 实例。

    Args:
        text (str): 显示文本。
        alignment (AlignmentFlag): 对齐方式。
        font (Font) : 字体。
        style (str) : 格式。

    Returns:
        QLabel: 配置好的 QLabel 实例。
    """
    label = QLabel()
    label.setText(text)

    if alignment:
        label.setAlignment(alignment)

    if font:
        label.setFont(font)

    if style:
        label.setStyleSheet(style)

    return label


def create_button(text="", style="padding: 8px;"):
    """
    创建并返回配置好的 QPushButton 实例。

    Args:
        text (str): 显示文本。
        style (str) : 格式。

    Returns:
        QPushButton: 配置好的 QPushButton 实例。
    """
    button = QPushButton()
    button.setText(text)

    if style:
        button.setStyleSheet("padding: 8px;")

    return button


def create_spin_box(spin_box_type, min_value=None, max_value=None, current_value=None, single_step=None,
                    decimals=None, suffix=None, alignment=None):
    """
    创建并返回 QSpinBox 或 QDoubleSpinBox 实例。

    Args:
        spin_box_type (type): 需要创建的部件类型，可以是 QSpinBox 或 QDoubleSpinBox。
        min_value (float): 最小值。
        max_value (float): 最大值。
        current_value (float): 初始值。
        single_step (float): 单步步长。
        decimals (int, optional): 小数位数（仅适用于 QDoubleSpinBox）。
        suffix (str, optional): 后缀文本，例如 "秒"。
        alignment (AlignmentFlag): 对齐方式。

    Returns:
        QSpinBox 或 QDoubleSpinBox: 配置好的 spin box 实例。
    """
    spin_box = spin_box_type()

    # 使用 is not None 来检查，因为 min_value 可能是 0
    if min_value is not None and max_value is not None:
        spin_box.setRange(min_value, max_value)
    elif min_value is not None:
        spin_box.setMinimum(min_value)
    elif max_value is not None:
        spin_box.setMaximum(max_value)

    if current_value is not None:
        spin_box.setValue(current_value)

    if single_step:
        spin_box.setSingleStep(single_step)

    if isinstance(spin_box, QDoubleSpinBox) and decimals is not None:
        spin_box.setDecimals(decimals)

    if suffix:
        spin_box.setSuffix(suffix)

    if alignment:
        spin_box.setAlignment(alignment)

    return spin_box


def create_combo_box(items=None, current_text=None):
    """
    创建并返回配置好的 QComboBox 实例。

    Args:
        items (list): 包含下拉选项的字符串列表。
        current_text (str): 要设置为当前选中的文本项。

    Returns:
        QComboBox: 配置好的 QComboBox 实例。
    """
    if items is None:
        items = []
    combo_box = QComboBox()
    combo_box.addItems(items)

    if current_text is not None:
        combo_box.setCurrentText(current_text)

    return combo_box


def create_line_edit(text="", alignment=None):
    """
    创建并返回配置好的 QLineEdit 实例。

    Args:
        text (str, optional): 初始文本内容。默认为空字符串。
        alignment (AlignmentFlag): 对齐方式。

    Returns:
        QLineEdit: 配置好的 QLineEdit 实例。
    """
    line_edit = QLineEdit()
    line_edit.setText(text)
    line_edit.setCursorPosition(0)

    if alignment:
        line_edit.setAlignment(alignment)

    return line_edit
