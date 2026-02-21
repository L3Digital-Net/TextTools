"""Main application entry point."""
import sys
import logging
from PySide6.QtWidgets import QApplication
from src.views.main_window import MainWindow
from src.viewmodels.main_viewmodel import MainViewModel
from src.services.example_service import ExampleService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_application() -> MainWindow:
    """Create and configure the application.

    This function demonstrates dependency injection:
    - Services are created first (bottom layer)
    - ViewModels receive services via constructor
    - Views receive ViewModels via constructor

    Returns:
        Configured MainWindow instance.
    """
    # Create services (infrastructure layer)
    example_service = ExampleService()

    # Create viewmodels (presentation layer)
    main_viewmodel = MainViewModel(example_service)

    # Create views (UI layer)
    main_window = MainWindow(main_viewmodel)

    return main_window


def main():
    """Application entry point."""
    logger.info("Starting application")

    app = QApplication(sys.argv)
    app.setApplicationName("TextTools")
    app.setOrganizationName("TextTools")

    main_window = create_application()
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
