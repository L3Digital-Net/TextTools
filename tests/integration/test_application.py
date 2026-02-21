"""Integration tests — real services, real models, mocked Qt.

These tests verify the full stack (FileService → ViewModel → signal) without
launching a real window. The view layer is excluded here; that's covered by
qt-pilot GUI tests.
"""

import pytest

from src.models.cleaning_options import CleaningOptions
from src.services.file_service import FileService
from src.services.text_processing_service import TextProcessingService
from src.viewmodels.main_viewmodel import MainViewModel


@pytest.fixture
def file_svc():
    return FileService()


@pytest.fixture
def text_svc():
    return TextProcessingService()


@pytest.fixture
def vm(file_svc, text_svc, qapp):
    return MainViewModel(file_svc, text_svc)


class TestLoadSaveWorkflow:
    def test_load_real_file(self, vm, tmp_path, qtbot):
        f = tmp_path / "sample.txt"
        f.write_text("hello integration", encoding="utf-8")

        with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
            vm.load_file(str(f))

        assert blocker.args[0] == "hello integration"

    def test_save_then_reload(self, vm, tmp_path, qtbot):
        filepath = str(tmp_path / "out.txt")

        with qtbot.waitSignal(vm.file_saved, timeout=1000):
            vm.save_file(filepath, "saved content")

        with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
            vm.load_file(filepath)

        assert blocker.args[0] == "saved content"


class TestCleaningWorkflow:
    def test_load_then_clean_then_save(self, vm, tmp_path, qtbot):
        f = tmp_path / "dirty.txt"
        f.write_text("\n  hello    world  \n\n", encoding="utf-8")

        # Load
        with qtbot.waitSignal(vm.document_loaded):
            vm.load_file(str(f))

        # Clean all options
        opts = CleaningOptions(
            trim_whitespace=True, clean_whitespace=True, remove_tabs=False
        )
        with qtbot.waitSignal(vm.content_updated, timeout=1000) as blocker:
            vm.apply_cleaning(opts)

        cleaned = blocker.args[0]
        # trim_whitespace removes leading/trailing blank lines and trailing spaces per
        # line but not leading spaces. clean_whitespace collapses runs of 2+ spaces to
        # one. So "  hello    world" → " hello world" (leading two spaces → one).
        assert cleaned == " hello world"

        # Save cleaned result
        save_path = str(tmp_path / "clean.txt")
        with qtbot.waitSignal(vm.file_saved, timeout=1000):
            vm.save_file(save_path, cleaned)

        assert (tmp_path / "clean.txt").read_text(encoding="utf-8") == " hello world"


class TestReplaceAllWorkflow:
    def test_replace_all_end_to_end(self, vm, tmp_path, qtbot):
        f = tmp_path / "replace.txt"
        f.write_text("foo bar foo baz foo", encoding="utf-8")

        with qtbot.waitSignal(vm.document_loaded):
            vm.load_file(str(f))

        with qtbot.waitSignal(vm.content_updated, timeout=1000) as blocker:
            vm.replace_all("foo", "qux")

        assert blocker.args[0] == "qux bar qux baz qux"
