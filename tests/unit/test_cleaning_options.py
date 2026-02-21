"""Unit tests for CleaningOptions model."""

from src.models.cleaning_options import CleaningOptions


class TestCleaningOptions:
    def test_all_options_default_to_false(self):
        opts = CleaningOptions()
        assert opts.trim_whitespace is False
        assert opts.clean_whitespace is False
        assert opts.remove_tabs is False

    def test_options_can_be_set(self):
        opts = CleaningOptions(trim_whitespace=True, remove_tabs=True)
        assert opts.trim_whitespace is True
        assert opts.clean_whitespace is False
        assert opts.remove_tabs is True

    def test_all_options_enabled(self):
        opts = CleaningOptions(
            trim_whitespace=True,
            clean_whitespace=True,
            remove_tabs=True,
        )
        assert opts.trim_whitespace is True
        assert opts.clean_whitespace is True
        assert opts.remove_tabs is True
