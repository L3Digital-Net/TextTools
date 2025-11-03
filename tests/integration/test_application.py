"""Integration tests for the application.

Integration tests verify that multiple components work together correctly.
These tests may instantiate real objects instead of mocks.
"""
import pytest
from src.services.example_service import ExampleService
from src.viewmodels.main_viewmodel import MainViewModel
from src.models.example_model import ExampleModel


class TestApplicationIntegration:
    """Integration tests for main application flow."""

    @pytest.fixture
    def service(self):
        """Create a real service instance.

        Returns:
            ExampleService instance.
        """
        return ExampleService()

    @pytest.fixture
    def viewmodel(self, service, qapp):
        """Create a ViewModel with real service.

        Args:
            service: Real ExampleService fixture.
            qapp: QApplication fixture.

        Returns:
            MainViewModel instance.
        """
        return MainViewModel(service)

    def test_load_data_end_to_end(self, viewmodel, qtbot):
        """Test loading data through the full stack.

        This test verifies:
        - ViewModel calls Service
        - Service returns Models
        - ViewModel processes Models
        - ViewModel emits correct signals
        """
        # Arrange
        with qtbot.waitSignal(viewmodel.data_loaded, timeout=1000) as blocker:
            # Act
            viewmodel.load_data()

        # Assert
        display_items = blocker.args[0]
        assert len(display_items) == 3  # Service returns 3 items
        assert all(isinstance(item, str) for item in display_items)

    def test_service_returns_valid_models(self, service):
        """Test that service returns valid model instances."""
        # Act
        models = service.fetch_data()

        # Assert
        assert len(models) == 3
        assert all(isinstance(model, ExampleModel) for model in models)
        assert all(model.validate() for model in models)

    def test_full_workflow_with_real_components(self, viewmodel, qtbot):
        """Test complete workflow: load, get details, clear.

        This test exercises the full application flow with real components.
        """
        # Act & Assert - Load data
        with qtbot.waitSignal(viewmodel.data_loaded, timeout=1000):
            viewmodel.load_data()

        # Act & Assert - Get details
        with qtbot.waitSignal(viewmodel.status_changed, timeout=1000) as blocker:
            viewmodel.get_item_details(0)

        details = blocker.args[0]
        assert "ID:" in details

        # Act & Assert - Clear data
        with qtbot.waitSignal(viewmodel.data_loaded, timeout=1000) as blocker:
            viewmodel.clear_data()

        assert blocker.args[0] == []
