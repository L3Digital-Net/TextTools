"""Application entry point — composition root for TextTools.

Creates services → injects into ViewModel → injects into View.
This is the only place in the app where concrete types are instantiated.
"""

import logging
import sys

from PySide6.QtWidgets import QApplication

from src.services.file_service import FileService
from src.services.text_processing_service import TextProcessingService
from src.viewmodels.main_viewmodel import MainViewModel
from src.views.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def create_application() -> MainWindow:
    """Wire services → viewmodel → view and return the main window."""
    file_service = FileService()
    text_service = TextProcessingService()
    viewmodel = MainViewModel(file_service, text_service)
    return MainWindow(viewmodel)


def main() -> None:
    """Application entry point."""
    logger.info("Starting TextTools")
    app = QApplication(sys.argv)
    app.setApplicationName("TextTools")
    app.setOrganizationName("TextTools")

    window = create_application()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
