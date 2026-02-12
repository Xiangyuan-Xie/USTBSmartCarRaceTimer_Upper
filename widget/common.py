from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFontMetrics, QPainter
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QLabel, QLineEdit, QPushButton, QWidget


class MarqueeLabel(QWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._text = text
        self._offset = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._scroll)
        self._timer.start(30)  # Update every 30ms

    def setText(self, text):
        self._text = text
        self._offset = 0
        self.update()

    def text(self):
        return self._text

    def _scroll(self):
        if not self.isVisible():
            return

        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(self._text)

        if text_width > self.width():
            self._offset -= 1
            if self._offset < -text_width:
                self._offset = self.width()
            self.update()
        else:
            if self._offset != 0:
                self._offset = 0
                self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(self._text)

        # Center vertically
        y = (self.height() + fm.ascent() - fm.descent()) // 2

        if text_width > self.width():
            # Draw scrolling text
            painter.drawText(self._offset, y, self._text)
        else:
            # Draw centered text
            x = (self.width() - text_width) // 2
            painter.drawText(x, y, self._text)


def create_label(text="", alignment=Qt.AlignmentFlag.AlignCenter, font=None, style=None):
    """
    Create and return a configured QLabel instance.

    Args:
        text (str): Display text.
        alignment (AlignmentFlag): Alignment.
        font (Font): Font.
        style (str): Style.

    Returns:
        QLabel: Configured QLabel instance.
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
    Create and return a configured QPushButton instance.

    Args:
        text (str): Display text.
        style (str): Style.

    Returns:
        QPushButton: Configured QPushButton instance.
    """
    button = QPushButton()
    button.setText(text)

    if style:
        button.setStyleSheet("padding: 8px;")

    return button


def create_spin_box(
    spin_box_type,
    min_value=None,
    max_value=None,
    current_value=None,
    single_step=None,
    decimals=None,
    suffix=None,
    alignment=None,
):
    """
    Create and return a QSpinBox or QDoubleSpinBox instance.

    Args:
        spin_box_type (type): Type of widget to create, can be QSpinBox or QDoubleSpinBox.
        min_value (float): Minimum value.
        max_value (float): Maximum value.
        current_value (float): Initial value.
        single_step (float): Step size.
        decimals (int, optional): Number of decimals (only for QDoubleSpinBox).
        suffix (str, optional): Suffix text, e.g., " seconds".
        alignment (AlignmentFlag): Alignment.

    Returns:
        QSpinBox or QDoubleSpinBox: Configured spin box instance.
    """
    spin_box = spin_box_type()

    # Use is not None to check, because min_value can be 0
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
    Create and return a configured QComboBox instance.

    Args:
        items (list): List of strings for dropdown options.
        current_text (str): Text item to set as currently selected.

    Returns:
        QComboBox: Configured QComboBox instance.
    """
    if items is None:
        items = []
    combo_box = QComboBox()
    combo_box.addItems(items)

    if current_text is not None:
        combo_box.setCurrentText(current_text)

    return combo_box


def create_line_edit(text="", alignment=None, placeholder=None):
    """
    Create and return a configured QLineEdit instance.

    Args:
        text (str, optional): Initial text content. Default is empty string.
        alignment (AlignmentFlag): Alignment.
        placeholder (str, optional): Placeholder text.

    Returns:
        QLineEdit: Configured QLineEdit instance.
    """
    line_edit = QLineEdit()
    line_edit.setText(text)
    line_edit.setCursorPosition(0)

    if alignment:
        line_edit.setAlignment(alignment)

    if placeholder:
        line_edit.setPlaceholderText(placeholder)

    return line_edit
