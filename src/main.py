"""Application entry point — composition root for TextTools.

Creates services → injects into ViewModel → injects into View.
This is the only place in the app where concrete types are instantiated.
"""

import logging
import sys
from pathlib import Path

# Insert project root so `from src.xxx` imports resolve regardless of how the
# script is invoked (python src/main.py, python -m src.main, full path, IDE).
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from PySide6.QtWidgets import QApplication  # noqa: E402

from src.services.file_service import FileService  # noqa: E402
from src.services.text_processing_service import TextProcessingService  # noqa: E402
from src.utils.constants import APP_NAME, APP_VERSION  # noqa: E402
from src.viewmodels.main_viewmodel import MainViewModel  # noqa: E402
from src.views.main_window import MainWindow  # noqa: E402

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


def main() -> None:  # pragma: no cover
    """Application entry point."""
    logger.info("Starting TextTools")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_NAME)

    window = create_application()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()
