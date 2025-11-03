"""Example ViewModel demonstrating MVVM pattern.

ViewModels contain presentation logic and mediate between Views and Models.
They inherit from QObject to use Qt's signal/slot mechanism.
"""
import logging
from PySide6.QtCore import QObject, Signal, Slot
from typing import List, Protocol
from src.models.example_model import ExampleModel


logger = logging.getLogger(__name__)


class ServiceProtocol(Protocol):
    """Protocol defining the service interface.

    This allows for dependency injection and easy testing with mocks.
    """

    def fetch_data(self) -> List[ExampleModel]:
        """Fetch data from service."""
        ...

    def save_data(self, model: ExampleModel) -> bool:
        """Save data to service."""
        ...


class MainViewModel(QObject):
    """Main application ViewModel.

    Signals:
        data_loaded: Emitted when data is successfully loaded.
        error_occurred: Emitted when an error occurs.
        status_changed: Emitted when status message changes.
    """

    # Define signals for state changes
    data_loaded = Signal(list)  # Emits list of display strings
    error_occurred = Signal(str)  # Emits error message
    status_changed = Signal(str)  # Emits status message

    def __init__(self, service: ServiceProtocol):
        """Initialize the ViewModel.

        Args:
            service: Service instance for data operations.
        """
        super().__init__()
        self._service = service
        self._models: List[ExampleModel] = []

    @Slot()
    def load_data(self) -> None:
        """Load data from service.

        Fetches data and emits appropriate signals based on result.
        """
        logger.info("Loading data")
        self.status_changed.emit("Loading data...")

        try:
            self._models = self._service.fetch_data()

            # Convert models to display strings
            display_items = [model.to_display_string() for model in self._models]

            self.data_loaded.emit(display_items)
            self.status_changed.emit(f"Loaded {len(self._models)} items")
            logger.info(f"Successfully loaded {len(self._models)} items")

        except Exception as e:
            error_msg = f"Failed to load data: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.status_changed.emit("Error loading data")

    @Slot(int)
    def get_item_details(self, index: int) -> None:
        """Get detailed information about an item.

        Args:
            index: Index of the item in the list.
        """
        if 0 <= index < len(self._models):
            model = self._models[index]
            details = (
                f"ID: {model.id}\n"
                f"Name: {model.name}\n"
                f"Value: {model.value}\n"
                f"Doubled: {model.calculate_doubled_value()}\n"
                f"Description: {model.description or 'N/A'}"
            )
            self.status_changed.emit(details)

    @Slot()
    def clear_data(self) -> None:
        """Clear all loaded data."""
        logger.info("Clearing data")
        self._models.clear()
        self.data_loaded.emit([])
        self.status_changed.emit("Data cleared")
