import sys
import warnings

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from widget.console import Console

warnings.filterwarnings("ignore", category=DeprecationWarning)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    console = Console()
    console.setWindowIcon(QIcon("icon.ico"))
    console.show()
    sys.exit(app.exec())
