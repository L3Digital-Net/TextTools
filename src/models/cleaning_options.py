"""CleaningOptions — configuration for text cleaning operations.

Passed from View → ViewModel → TextProcessingService. If fields change,
update MainWindow._collect_cleaning_options() and TextProcessingService.apply_options().
"""

from dataclasses import dataclass


@dataclass
class CleaningOptions:
    """Flags controlling which text cleaning operations to apply.

    Attributes:
        trim_whitespace: Strip leading/trailing blank lines; strip trailing
            spaces from each line.
        clean_whitespace: Collapse multiple consecutive spaces to one.
        remove_tabs: Strip leading tabs and spaces from the start of each line.
    """

    trim_whitespace: bool = False
    clean_whitespace: bool = False
    remove_tabs: bool = False
