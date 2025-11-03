"""Example service for external operations.

Services handle external integrations, file I/O, API calls, etc.
They are injected into ViewModels.
"""
import logging
from typing import List
from src.models.example_model import ExampleModel


logger = logging.getLogger(__name__)


class ExampleService:
    """Example service demonstrating external operations."""

    def __init__(self):
        """Initialize the service."""
        self._data_cache: List[ExampleModel] = []

    def fetch_data(self) -> List[ExampleModel]:
        """Fetch data from external source.

        In a real application, this would:
        - Connect to a database
        - Make API calls
        - Read from files

        Returns:
            List of ExampleModel instances.

        Raises:
            ConnectionError: If external source is unavailable.
        """
        logger.info("Fetching data from service")

        try:
            # Simulate data fetching
            # In real app, replace with actual data source
            data = [
                ExampleModel(1, "Item One", 100.0, "First item"),
                ExampleModel(2, "Item Two", 200.0, "Second item"),
                ExampleModel(3, "Item Three", 300.0, "Third item"),
            ]

            self._data_cache = data
            logger.info(f"Successfully fetched {len(data)} items")
            return data

        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            raise ConnectionError(f"Service unavailable: {e}")

    def save_data(self, model: ExampleModel) -> bool:
        """Save data to external source.

        Args:
            model: Model instance to save.

        Returns:
            True if save was successful.

        Raises:
            ValueError: If model validation fails.
        """
        if not model.validate():
            raise ValueError("Invalid model data")

        logger.info(f"Saving model: {model.name}")

        # Simulate saving
        # In real app, replace with actual data persistence
        return True
