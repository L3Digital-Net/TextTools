"""TextProcessingService — stateless text cleaning operations.

No Qt imports. No file I/O. Each method is a pure function wrapped in a class
for dependency injection. Called by MainViewModel.apply_cleaning().
If the CleaningOptions fields change, update apply_options() below.
"""

import logging
import re

from src.models.cleaning_options import CleaningOptions

logger = logging.getLogger(__name__)


class TextProcessingService:
    """Stateless text cleaning and manipulation.

    All methods take a str and return a str; they have no side effects.
    """

    def trim_whitespace(self, text: str) -> str:
        """Strip leading/trailing blank lines; strip trailing spaces from each line."""
        lines = text.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(line.rstrip() for line in lines)

    def clean_whitespace(self, text: str) -> str:
        """Collapse two or more consecutive spaces to a single space on each line."""
        lines = text.splitlines()
        return "\n".join(re.sub(r" {2,}", " ", line) for line in lines)

    def remove_tabs(self, text: str) -> str:
        """Strip leading tabs and spaces from the start of each line."""
        lines = text.splitlines()
        return "\n".join(line.lstrip(" \t") for line in lines)

    def apply_options(self, text: str, options: CleaningOptions) -> str:
        """Apply enabled cleaning operations in a fixed order.

        Order: trim_whitespace → clean_whitespace → remove_tabs.
        This order is intentional: trimming first removes boundary noise before
        whitespace normalization runs on the meaningful content.
        """
        if options.trim_whitespace:
            text = self.trim_whitespace(text)
        if options.clean_whitespace:
            text = self.clean_whitespace(text)
        if options.remove_tabs:
            text = self.remove_tabs(text)
        return text
