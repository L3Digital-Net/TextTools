"""Unit tests for MainViewModel.

Services are mocked so these tests run without file system access.
Uses qtbot (pytest-qt) for signal assertion.
"""

from unittest.mock import MagicMock

import pytest

from src.models.cleaning_options import CleaningOptions
from src.models.text_document import TextDocument
from src.viewmodels.main_viewmodel import MainViewModel


@pytest.fixture
def mock_file_svc():
    svc = MagicMock()
    svc.open_file.return_value = TextDocument(
        filepath="/tmp/test.txt", content="hello world", encoding="utf-8"
    )
    return svc


@pytest.fixture
def mock_text_svc():
    svc = MagicMock()
    svc.apply_options.return_value = "cleaned text"
    return svc


@pytest.fixture
def vm(mock_file_svc, mock_text_svc, qapp):
    return MainViewModel(mock_file_svc, mock_text_svc)


class TestLoadFile:
    def test_calls_file_service(self, vm, mock_file_svc):
        vm.load_file("/tmp/test.txt")
        mock_file_svc.open_file.assert_called_once_with("/tmp/test.txt")

    def test_emits_document_loaded_with_content(self, vm, qtbot):
        with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
            vm.load_file("/tmp/test.txt")
        assert blocker.args[0] == "hello world"

    def test_emits_encoding_detected(self, vm, qtbot):
        with qtbot.waitSignal(vm.encoding_detected, timeout=1000) as blocker:
            vm.load_file("/tmp/test.txt")
        assert blocker.args[0] == "utf-8"

    def test_emits_error_on_file_not_found(self, vm, mock_file_svc, qtbot):
        mock_file_svc.open_file.side_effect = FileNotFoundError("not found")
        with qtbot.waitSignal(vm.error_occurred, timeout=1000) as blocker:
            vm.load_file("/tmp/missing.txt")
        assert "Cannot open file" in blocker.args[0]

    def test_emits_status_changed(self, vm, qtbot):
        messages = []
        vm.status_changed.connect(messages.append)
        vm.load_file("/tmp/test.txt")
        qtbot.wait(10)
        assert any("test.txt" in m for m in messages)


class TestSaveFile:
    def test_calls_file_service_save(self, vm, mock_file_svc, qtbot):
        # Load first to set current encoding
        vm.load_file("/tmp/test.txt")
        vm.save_file("/tmp/out.txt", "content to save")
        assert mock_file_svc.save_file.called

    def test_emits_file_saved_signal(self, vm, qtbot):
        with qtbot.waitSignal(vm.file_saved, timeout=1000) as blocker:
            vm.save_file("/tmp/out.txt", "content")
        assert blocker.args[0] == "/tmp/out.txt"

    def test_emits_error_on_permission_denied(self, vm, mock_file_svc, qtbot):
        mock_file_svc.save_file.side_effect = PermissionError("denied")
        with qtbot.waitSignal(vm.error_occurred, timeout=1000) as blocker:
            vm.save_file("/tmp/out.txt", "content")
        assert "Cannot save file" in blocker.args[0]


class TestApplyCleaning:
    def test_calls_text_service_with_options(self, vm, mock_file_svc, mock_text_svc):
        vm.load_file("/tmp/test.txt")
        opts = CleaningOptions(trim_whitespace=True)
        vm.apply_cleaning(opts)
        mock_text_svc.apply_options.assert_called_once_with("hello world", opts)

    def test_emits_content_updated_with_cleaned_text(self, vm, qtbot):
        vm.load_file("/tmp/test.txt")
        opts = CleaningOptions(trim_whitespace=True)
        with qtbot.waitSignal(vm.content_updated, timeout=1000) as blocker:
            vm.apply_cleaning(opts)
        assert blocker.args[0] == "cleaned text"

    def test_no_op_when_no_document_loaded(self, vm, mock_text_svc, qtbot):
        vm.apply_cleaning(CleaningOptions(trim_whitespace=True))
        mock_text_svc.apply_options.assert_not_called()

    def test_uses_current_text_when_provided(self, vm, mock_file_svc, mock_text_svc):
        """apply_cleaning should clean the passed text, not _current_document.content."""
        vm.load_file("/tmp/test.txt")  # loads "hello world"
        opts = CleaningOptions(trim_whitespace=True)
        vm.apply_cleaning(opts, current_text="  edited text  ")
        # text service should have received the editor text, not "hello world"
        mock_text_svc.apply_options.assert_called_once_with("  edited text  ", opts)


class TestReplaceAll:
    def test_replaces_all_occurrences_in_content(self, vm, qtbot):
        vm.load_file("/tmp/test.txt")  # content = "hello world"
        with qtbot.waitSignal(vm.content_updated, timeout=1000) as blocker:
            vm.replace_all("hello", "goodbye")
        assert blocker.args[0] == "goodbye world"

    def test_emits_status_with_count(self, vm, qtbot):
        vm.load_file("/tmp/test.txt")
        messages = []
        vm.status_changed.connect(messages.append)
        vm.replace_all("hello", "goodbye")
        qtbot.wait(10)
        assert any("1 occurrence" in m for m in messages)

    def test_no_op_when_no_document(self, vm, qtbot):
        # Should not emit content_updated when no document
        emitted = []
        vm.content_updated.connect(emitted.append)
        vm.replace_all("x", "y")
        qtbot.wait(10)
        assert emitted == []

    def test_no_op_for_empty_find_term(self, vm, qtbot):
        vm.load_file("/tmp/test.txt")
        emitted = []
        vm.content_updated.connect(emitted.append)
        qtbot.wait(10)
        emitted.clear()
        vm.replace_all("", "replacement")
        qtbot.wait(10)
        assert emitted == []

    def test_replace_all_uses_current_text_when_provided(self, vm, qtbot):
        """replace_all should operate on the passed text, not _current_document.content."""
        vm.load_file("/tmp/test.txt")  # loads "hello world"
        with qtbot.waitSignal(vm.content_updated, timeout=1000) as blocker:
            vm.replace_all("hello", "goodbye", current_text="hello hello")
        assert blocker.args[0] == "goodbye goodbye"


class TestConvertToUtf8:
    def test_saves_file_with_utf8_encoding(self, vm, mock_file_svc, qtbot):
        """convert_to_utf8 must call save_file with encoding='utf-8'."""
        mock_file_svc.open_file.return_value = TextDocument(
            filepath="/tmp/latin.txt", content="caf\u00e9", encoding="ISO-8859-1"
        )
        vm.load_file("/tmp/latin.txt")
        vm.convert_to_utf8("café")
        saved_doc = mock_file_svc.save_file.call_args[0][0]
        assert saved_doc.encoding == "utf-8"
        assert saved_doc.content == "café"

    def test_emits_encoding_detected_utf8(self, vm, mock_file_svc, qtbot):
        """convert_to_utf8 must emit encoding_detected('utf-8')."""
        mock_file_svc.open_file.return_value = TextDocument(
            filepath="/tmp/latin.txt", content="caf\u00e9", encoding="ISO-8859-1"
        )
        vm.load_file("/tmp/latin.txt")
        with qtbot.waitSignal(vm.encoding_detected, timeout=1000) as blocker:
            vm.convert_to_utf8("café")
        assert blocker.args[0] == "utf-8"

    def test_emits_file_saved(self, vm, mock_file_svc, qtbot):
        """convert_to_utf8 must emit file_saved after a successful save."""
        mock_file_svc.open_file.return_value = TextDocument(
            filepath="/tmp/latin.txt", content="caf\u00e9", encoding="ISO-8859-1"
        )
        vm.load_file("/tmp/latin.txt")
        with qtbot.waitSignal(vm.file_saved, timeout=1000) as blocker:
            vm.convert_to_utf8("café")
        assert blocker.args[0] == "/tmp/latin.txt"

    def test_no_op_when_already_utf8(self, vm, mock_file_svc, qtbot):
        """convert_to_utf8 must not save when encoding is already utf-8."""
        mock_file_svc.open_file.return_value = TextDocument(
            filepath="/tmp/utf8.txt", content="hello", encoding="utf-8"
        )
        vm.load_file("/tmp/utf8.txt")
        with qtbot.waitSignal(vm.status_changed, timeout=1000) as blocker:
            vm.convert_to_utf8("hello")
        mock_file_svc.save_file.assert_not_called()
        assert "already" in blocker.args[0].lower()

    def test_no_op_when_no_document(self, vm, qtbot):
        """convert_to_utf8 with no loaded document emits status_changed."""
        with qtbot.waitSignal(vm.status_changed, timeout=1000) as blocker:
            vm.convert_to_utf8("some text")
        assert "no document" in blocker.args[0].lower()

    def test_no_op_when_utf8_with_bom(self, vm, mock_file_svc, qtbot):
        """UTF-8-SIG (BOM) files must be treated as already UTF-8."""
        mock_file_svc.open_file.return_value = TextDocument(
            filepath="/tmp/bom.txt", content="hello", encoding="UTF-8-SIG"
        )
        vm.load_file("/tmp/bom.txt")
        vm.convert_to_utf8("hello")
        mock_file_svc.save_file.assert_not_called()

    def test_emits_error_on_save_failure(self, vm, mock_file_svc, qtbot):
        """convert_to_utf8 must emit error_occurred when save_file raises."""
        mock_file_svc.open_file.return_value = TextDocument(
            filepath="/tmp/latin.txt", content="caf\u00e9", encoding="ISO-8859-1"
        )
        vm.load_file("/tmp/latin.txt")
        mock_file_svc.save_file.side_effect = PermissionError("read-only")
        with qtbot.waitSignal(vm.error_occurred, timeout=1000) as blocker:
            vm.convert_to_utf8("café")


class TestMergeQueue:
    """Tests for the file merge queue slots."""

    def test_add_current_to_merge(self, vm, mock_file_svc, qtbot):
        vm.load_file("/tmp/test.txt")
        with qtbot.waitSignal(vm.merge_list_changed, timeout=1000) as blocker:
            vm.add_current_to_merge()
        assert blocker.args[0] == ["test.txt"]

    def test_add_current_no_file_emits_error(self, vm, qtbot):
        with qtbot.waitSignal(vm.error_occurred, timeout=1000) as blocker:
            vm.add_current_to_merge()
        assert "No file loaded" in blocker.args[0]

    def test_add_files_to_merge(self, vm, qtbot):
        with qtbot.waitSignal(vm.merge_list_changed, timeout=1000) as blocker:
            vm.add_files_to_merge(["/tmp/a.txt", "/tmp/b.txt"])
        assert blocker.args[0] == ["a.txt", "b.txt"]

    def test_duplicate_ignored(self, vm, qtbot):
        vm.add_files_to_merge(["/tmp/a.txt"])
        names: list[list[str]] = []
        vm.merge_list_changed.connect(names.append)
        vm.add_files_to_merge(["/tmp/a.txt"])  # duplicate — should not emit
        assert names == []

    def test_remove_from_merge(self, vm, qtbot):
        vm.add_files_to_merge(["/tmp/a.txt", "/tmp/b.txt"])
        with qtbot.waitSignal(vm.merge_list_changed, timeout=1000) as blocker:
            vm.remove_from_merge(0)
        assert blocker.args[0] == ["b.txt"]

    def test_move_merge_item_forward(self, vm, qtbot):
        vm.add_files_to_merge(["/tmp/a.txt", "/tmp/b.txt", "/tmp/c.txt"])
        with qtbot.waitSignal(vm.merge_list_changed, timeout=1000) as blocker:
            vm.move_merge_item(0, 2)  # move a after b
        assert blocker.args[0] == ["b.txt", "a.txt", "c.txt"]

    def test_move_merge_item_backward(self, vm, qtbot):
        vm.add_files_to_merge(["/tmp/a.txt", "/tmp/b.txt", "/tmp/c.txt"])
        with qtbot.waitSignal(vm.merge_list_changed, timeout=1000) as blocker:
            vm.move_merge_item(2, 0)  # move c before a
        assert blocker.args[0] == ["c.txt", "a.txt", "b.txt"]

    def test_execute_merge_emits_document_loaded(
        self, vm, mock_file_svc, mock_text_svc, qtbot
    ):
        mock_text_svc.merge_documents.return_value = "merged content"
        vm.add_files_to_merge(["/tmp/a.txt", "/tmp/b.txt"])
        with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
            vm.execute_merge()
        assert blocker.args[0] == "merged content"

    def test_execute_merge_empty_list_emits_error(self, vm, qtbot):
        with qtbot.waitSignal(vm.error_occurred, timeout=1000) as blocker:
            vm.execute_merge()
        assert "No files in merge list" in blocker.args[0]

    def test_execute_merge_file_read_error(self, vm, mock_file_svc, qtbot):
        vm.add_files_to_merge(["/tmp/missing.txt"])
        mock_file_svc.open_file.side_effect = FileNotFoundError("gone")
        with qtbot.waitSignal(vm.error_occurred, timeout=1000) as blocker:
            vm.execute_merge()
        assert "Cannot read" in blocker.args[0]

    def test_set_merge_separator(self, vm, mock_file_svc, mock_text_svc, qtbot):
        vm.add_files_to_merge(["/tmp/a.txt"])
        vm.set_merge_separator("---")
        vm.execute_merge()
        mock_text_svc.merge_documents.assert_called_once()
        _, sep = mock_text_svc.merge_documents.call_args[0]
        assert sep == "---"
