"""DeviceProbe - Multi-Device Detection & Test Platform.

Entry point for the desktop application.
"""

import logging
import sys

from PySide6.QtWidgets import QApplication

from app.controllers.app_controller import AppController
from app.ui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("deviceprobe.log", mode="a"),
    ],
)
logger = logging.getLogger("DeviceProbe")


def main() -> int:
    logger.info("Starting DeviceProbe")

    app = QApplication(sys.argv)
    app.setApplicationName("DeviceProbe")
    app.setOrganizationName("DeviceProbe")

    controller = AppController()
    window = MainWindow(controller)
    window.show()

    logger.info("Application ready")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
