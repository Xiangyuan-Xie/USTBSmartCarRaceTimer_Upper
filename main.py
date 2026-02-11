import sys
import warnings

from PySide6.QtGui import QIcon

from widget.console import *

warnings.filterwarnings("ignore", category=DeprecationWarning)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    console = Console()
    console.setWindowIcon(QIcon("icon.ico"))
    console.show()
    sys.exit(app.exec())
