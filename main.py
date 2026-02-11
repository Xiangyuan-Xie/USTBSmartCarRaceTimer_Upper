import sys
import warnings

from loguru import logger
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from widget.console import Console

# Configure loguru
logger.remove()
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    ),
)

warnings.filterwarnings("ignore", category=DeprecationWarning)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    console = Console()
    console.setWindowIcon(QIcon("icon.ico"))
    console.show()
    sys.exit(app.exec())
