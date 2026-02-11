from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class RoundIndicator(QWidget):
    def __init__(self, color="red", size=20, margin=1, parent=None):
        super().__init__(parent)
        self._color = QColor(color)  # Set default color
        self.setFixedSize(size, size)  # Set fixed size for the widget
        self.margin = margin  # Set margin

    def setColor(self, color):
        self._color = QColor(color)
        self.update()  # Repaint the widget

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # Enable antialiasing
        painter.setBrush(self._color)  # Set fill color
        painter.setPen(Qt.PenStyle.NoPen)  # No border

        # Ensure the circle is in the center and has margin
        diameter = min(self.width(), self.height()) - 2 * self.margin  # Subtract margin
        rect = QRect(self.margin, self.margin, diameter, diameter)  # Drawing area
        rect.moveCenter(self.rect().center())  # Ensure circle is centered

        painter.drawEllipse(rect)  # Draw circle
