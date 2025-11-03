"""Unit tests for ExampleModel.

These tests demonstrate:
- Arrange-Act-Assert pattern
- Testing pure Python models without Qt
- Testing both success and failure cases
"""
import pytest
from src.models.example_model import ExampleModel


class TestExampleModel:
    """Test suite for ExampleModel."""

    @pytest.fixture
    def valid_model(self, example_model_data):
        """Create a valid model instance for testing.

        Args:
            example_model_data: Fixture providing sample data.

        Returns:
            ExampleModel instance.
        """
        return ExampleModel(**example_model_data)

    def test_model_initialization(self, example_model_data):
        """Test that model initializes correctly with valid data."""
        # Arrange & Act
        model = ExampleModel(**example_model_data)

        # Assert
        assert model.id == 1
        assert model.name == "Test Item"
        assert model.value == 100.0
        assert model.description == "Test description"

    def test_validate_returns_true_for_valid_data(self, valid_model):
        """Test that validate returns True for valid data."""
        # Act
        result = valid_model.validate()

        # Assert
        assert result is True

    def test_validate_returns_false_for_invalid_id(self):
        """Test that validate returns False when id is invalid."""
        # Arrange
        model = ExampleModel(id=0, name="Test", value=100.0)

        # Act
        result = model.validate()

        # Assert
        assert result is False

    def test_validate_returns_false_for_empty_name(self):
        """Test that validate returns False when name is empty."""
        # Arrange
        model = ExampleModel(id=1, name="", value=100.0)

        # Act
        result = model.validate()

        # Assert
        assert result is False

    def test_validate_returns_false_for_negative_value(self):
        """Test that validate returns False when value is negative."""
        # Arrange
        model = ExampleModel(id=1, name="Test", value=-10.0)

        # Act
        result = model.validate()

        # Assert
        assert result is False

    def test_calculate_doubled_value(self, valid_model):
        """Test that calculate_doubled_value returns correct result."""
        # Act
        result = valid_model.calculate_doubled_value()

        # Assert
        assert result == 200.0

    def test_to_display_string_with_description(self, valid_model):
        """Test display string generation with description."""
        # Act
        result = valid_model.to_display_string()

        # Assert
        assert "Test Item" in result
        assert "100.0" in result
        assert "Test description" in result

    def test_to_display_string_without_description(self):
        """Test display string generation without description."""
        # Arrange
        model = ExampleModel(id=1, name="Test", value=50.0)

        # Act
        result = model.to_display_string()

        # Assert
        assert "Test" in result
        assert "50.0" in result
        assert " - " not in result  # No description separator

    def test_description_is_optional(self):
        """Test that description parameter is optional."""
        # Arrange & Act
        model = ExampleModel(id=1, name="Test", value=100.0)

        # Assert
        assert model.description is None
