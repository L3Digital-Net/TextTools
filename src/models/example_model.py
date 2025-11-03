"""Example data model demonstrating MVVM pattern.

This module contains pure Python classes with no Qt dependencies.
Models represent domain entities and business logic.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExampleModel:
    """Example domain model.

    Attributes:
        id: Unique identifier.
        name: Display name.
        value: Numeric value.
        description: Optional description.
    """

    id: int
    name: str
    value: float
    description: Optional[str] = None

    def validate(self) -> bool:
        """Validate model data.

        Returns:
            True if data is valid, False otherwise.
        """
        return (
            self.id > 0 and
            len(self.name) > 0 and
            self.value >= 0
        )

    def calculate_doubled_value(self) -> float:
        """Example business logic method.

        Returns:
            Double the current value.
        """
        return self.value * 2

    def to_display_string(self) -> str:
        """Convert model to display string.

        Returns:
            Formatted string representation.
        """
        desc = f" - {self.description}" if self.description else ""
        return f"{self.name}: {self.value}{desc}"
