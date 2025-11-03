"""Unit tests for MainViewModel.

These tests demonstrate:
- Testing ViewModels with pytest-qt
- Using mocks to isolate ViewModel from services
- Testing signal emission
- Testing error handling
"""
import pytest
from unittest.mock import Mock
from src.viewmodels.main_viewmodel import MainViewModel
from src.models.example_model import ExampleModel


class TestMainViewModel:
    """Test suite for MainViewModel."""

    @pytest.fixture
    def mock_service(self, mocker):
        """Create a mock service for testing.

        Args:
            mocker: pytest-mock fixture.

        Returns:
            Mock service instance.
        """
        service = mocker.Mock()
        service.fetch_data.return_value = [
            ExampleModel(1, "Item 1", 100.0),
            ExampleModel(2, "Item 2", 200.0),
        ]
        return service

    @pytest.fixture
    def viewmodel(self, mock_service, qapp):
        """Create a ViewModel instance for testing.

        Args:
            mock_service: Mock service fixture.
            qapp: QApplication fixture.

        Returns:
            MainViewModel instance.
        """
        return MainViewModel(mock_service)

    def test_initialization(self, viewmodel):
        """Test that ViewModel initializes correctly."""
        # Assert
        assert viewmodel is not None
        assert hasattr(viewmodel, 'data_loaded')
        assert hasattr(viewmodel, 'error_occurred')
        assert hasattr(viewmodel, 'status_changed')

    def test_load_data_calls_service(self, viewmodel, mock_service):
        """Test that load_data calls the service."""
        # Act
        viewmodel.load_data()

        # Assert
        mock_service.fetch_data.assert_called_once()

    def test_load_data_emits_data_loaded_signal(self, viewmodel, qtbot):
        """Test that load_data emits data_loaded signal."""
        # Arrange
        with qtbot.waitSignal(viewmodel.data_loaded, timeout=1000) as blocker:
            # Act
            viewmodel.load_data()

        # Assert
        assert len(blocker.args[0]) == 2  # Two items loaded

    def test_load_data_emits_status_changed_signal(self, viewmodel, qtbot):
        """Test that load_data emits status_changed signal."""
        # Arrange - collect all emitted signals
        status_messages = []
        viewmodel.status_changed.connect(lambda msg: status_messages.append(msg))

        # Act
        viewmodel.load_data()
        qtbot.wait(10)  # Brief wait for all signals to process

        # Assert - should have emitted loading and completion messages
        assert len(status_messages) >= 2
        assert "Loading data..." in status_messages[0]
        assert "Loaded" in status_messages[1]
        assert "items" in status_messages[1]

    def test_load_data_handles_service_error(self, viewmodel, mock_service, qtbot):
        """Test that load_data handles service errors gracefully."""
        # Arrange
        mock_service.fetch_data.side_effect = ConnectionError("Service unavailable")

        with qtbot.waitSignal(viewmodel.error_occurred, timeout=1000) as blocker:
            # Act
            viewmodel.load_data()

        # Assert
        assert "Failed to load data" in blocker.args[0]

    def test_clear_data_emits_empty_list(self, viewmodel, qtbot):
        """Test that clear_data emits empty list."""
        # Arrange
        viewmodel.load_data()  # Load some data first

        with qtbot.waitSignal(viewmodel.data_loaded, timeout=1000) as blocker:
            # Act
            viewmodel.clear_data()

        # Assert
        assert blocker.args[0] == []

    def test_clear_data_emits_status_message(self, viewmodel, qtbot):
        """Test that clear_data emits status message."""
        # Arrange
        with qtbot.waitSignal(viewmodel.status_changed, timeout=1000) as blocker:
            # Act
            viewmodel.clear_data()

        # Assert
        assert blocker.args[0] == "Data cleared"

    def test_get_item_details_emits_details(self, viewmodel, qtbot):
        """Test that get_item_details emits item details."""
        # Arrange
        viewmodel.load_data()  # Load data first

        with qtbot.waitSignal(viewmodel.status_changed, timeout=1000) as blocker:
            # Act
            viewmodel.get_item_details(0)

        # Assert
        details = blocker.args[0]
        assert "ID:" in details
        assert "Name:" in details
        assert "Value:" in details

    def test_get_item_details_handles_invalid_index(self, viewmodel, qtbot):
        """Test that get_item_details handles invalid index gracefully."""
        # Arrange
        viewmodel.load_data()

        # Act - should not crash or emit signal for invalid index
        viewmodel.get_item_details(999)

        # Assert - no exception raised, execution completes
        assert True

    def test_data_loaded_signal_contains_display_strings(self, viewmodel, qtbot):
        """Test that data_loaded signal contains properly formatted strings."""
        # Arrange
        with qtbot.waitSignal(viewmodel.data_loaded, timeout=1000) as blocker:
            # Act
            viewmodel.load_data()

        # Assert
        display_items = blocker.args[0]
        assert isinstance(display_items, list)
        assert all(isinstance(item, str) for item in display_items)
        assert "Item 1: 100.0" in display_items[0]
