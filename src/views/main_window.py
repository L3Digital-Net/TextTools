"""Main application window — UI wiring only, no business logic.

Loads UI from src/views/ui/main_window.ui via QUiLoader. Widget objectNames
referenced here must match DESIGN.md Appendix A exactly. If the .ui file
changes objectNames, update findChild() calls below to match.

Signal flow:
  User action → View slot → ViewModel slot (via signal or direct call)
  ViewModel signal → View slot → widget update

Architecture note: MainWindow is a plain Python controller, not a QMainWindow
subclass. The .ui root IS a QMainWindow, so self.ui is the actual top-level
window. Embedding one QMainWindow inside another breaks sizing and menubar.
"""

import os
from typing import TypeVar, cast

from PySide6.QtCore import QDir, QFile, QModelIndex
from PySide6.QtGui import QAction
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFileSystemModel,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTreeView,
)

from src.models.cleaning_options import CleaningOptions
from src.viewmodels.main_viewmodel import MainViewModel

_W = TypeVar("_W")


def _require(widget: "_W | None", name: str) -> "_W":
    """Return widget or raise RuntimeError if findChild returned None.

    Catches objectName mismatches between main_window.py and the .ui file
    at startup rather than letting an AttributeError surface later.
    """
    if widget is None:
        raise RuntimeError(
            f"Required widget '{name}' not found in UI — check objectName in main_window.ui"
        )
    return widget


class MainWindow:
    """Main application window controller.

    Responsibilities:
    - Load main_window.ui and locate all named widgets
    - Wire user actions to ViewModel slots
    - Handle ViewModel signals to update the UI
    - Implement find/replace directly on QPlainTextEdit (Qt built-in)

    Not responsible for: file I/O, text processing, encoding detection.

    self.ui is the actual QMainWindow top-level window (the .ui root widget).
    This class is a plain Python controller — not a QMainWindow subclass.
    """

    def __init__(self, viewmodel: MainViewModel) -> None:
        self._viewmodel = viewmodel
        self._load_ui()
        self._setup_file_tree()
        self._connect_signals()

    def show(self) -> None:
        """Show the main application window."""
        self.ui.show()

    # ------------------------------------------------------------------ setup

    def _load_ui(self) -> None:
        """Load main_window.ui and resolve all widget references."""
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "main_window.ui")
        ui_file = QFile(ui_path)
        if not ui_file.open(QFile.OpenModeFlag.ReadOnly):
            raise RuntimeError(f"Cannot open UI file: {ui_path}")
        loader = QUiLoader()
        loaded = loader.load(ui_file)
        ui_file.close()
        if loaded is None:
            raise RuntimeError(f"QUiLoader failed to load UI file: {ui_path}")
        # The .ui root is QMainWindow — self.ui IS the top-level window.
        self.ui: QMainWindow = cast(QMainWindow, loaded)

        # Widget references — objectNames from DESIGN.md Appendix A
        self._plain_text_edit = _require(
            self.ui.findChild(QPlainTextEdit, "plainTextEdit"), "plainTextEdit"
        )
        self._file_name_edit = _require(
            self.ui.findChild(QLineEdit, "fileNameEdit"), "fileNameEdit"
        )
        self._save_button = _require(
            self.ui.findChild(QPushButton, "saveButton"), "saveButton"
        )
        self._file_tree_view = _require(
            self.ui.findChild(QTreeView, "fileTreeView"), "fileTreeView"
        )
        self._encoding_label = _require(
            self.ui.findChild(QLabel, "getEncodingFormatLabel"),
            "getEncodingFormatLabel",
        )
        self._trim_cb = _require(
            self.ui.findChild(QCheckBox, "trimWhiteSpaceCheckBox"),
            "trimWhiteSpaceCheckBox",
        )
        self._clean_cb = _require(
            self.ui.findChild(QCheckBox, "cleanWhiteSpaceCheckBox"),
            "cleanWhiteSpaceCheckBox",
        )
        self._remove_tabs_cb = _require(
            self.ui.findChild(QCheckBox, "removeTabsCheckBox"), "removeTabsCheckBox"
        )
        self._find_edit = _require(
            self.ui.findChild(QLineEdit, "findLineEdit"), "findLineEdit"
        )
        self._find_button = _require(
            self.ui.findChild(QPushButton, "findButton"), "findButton"
        )
        self._replace_edit = _require(
            self.ui.findChild(QLineEdit, "replaceLineEdit"), "replaceLineEdit"
        )
        self._replace_button = _require(
            self.ui.findChild(QPushButton, "replaceButton"), "replaceButton"
        )
        self._replace_all_button = _require(
            self.ui.findChild(QPushButton, "replaceAllButton"), "replaceAllButton"
        )
        self._convert_button = _require(
            self.ui.findChild(QPushButton, "convertEncodingButton"),
            "convertEncodingButton",
        )
        self._action_quit = _require(
            self.ui.findChild(QAction, "actionQuit"), "actionQuit"
        )
        self._action_save = _require(
            self.ui.findChild(QAction, "actionSave"), "actionSave"
        )
        self._action_open = _require(
            self.ui.findChild(QAction, "actionOpen"), "actionOpen"
        )
        self._action_save_as = _require(
            self.ui.findChild(QAction, "actionSave_as"), "actionSave_as"
        )
        self._action_about = _require(
            self.ui.findChild(QAction, "actionAbout"), "actionAbout"
        )
        self._action_preferences = _require(
            self.ui.findChild(QAction, "actionPreferences"), "actionPreferences"
        )

    def _setup_file_tree(self) -> None:
        """Configure QFileSystemModel rooted at the user's home directory."""
        self._fs_model = QFileSystemModel(self.ui)
        self._fs_model.setRootPath(QDir.homePath())
        self._file_tree_view.setModel(self._fs_model)
        self._file_tree_view.setRootIndex(self._fs_model.index(QDir.homePath()))
        # Hide size/type/date columns — name column only
        for col in range(1, self._fs_model.columnCount()):
            self._file_tree_view.hideColumn(col)

    def _connect_signals(self) -> None:
        """Wire UI events to ViewModel slots and ViewModel signals to UI handlers."""
        # File tree → load file (directories are filtered inside the slot)
        self._file_tree_view.clicked.connect(self._on_tree_item_clicked)

        # Save
        self._save_button.clicked.connect(self._on_save_clicked)

        # Cleaning: each checkbox triggers a fresh apply when a doc is loaded.
        # The checkboxes act as "apply now" toggles, not deferred configuration.
        self._trim_cb.stateChanged.connect(self._on_clean_requested)
        self._clean_cb.stateChanged.connect(self._on_clean_requested)
        self._remove_tabs_cb.stateChanged.connect(self._on_clean_requested)

        # Find / Replace
        self._find_button.clicked.connect(self._on_find_clicked)
        self._replace_button.clicked.connect(self._on_replace_clicked)
        self._replace_all_button.clicked.connect(self._on_replace_all_clicked)

        # Encoding convert is stubbed for v1
        self._convert_button.clicked.connect(
            lambda: self.ui.statusBar().showMessage("Encoding conversion — coming soon")
        )

        # Menu actions
        self._action_quit.triggered.connect(QApplication.quit)
        self._action_save.triggered.connect(self._on_save_clicked)
        self._action_open.triggered.connect(self._on_action_open)
        self._action_save_as.triggered.connect(
            lambda: self.ui.statusBar().showMessage("Save As — coming soon")
        )
        self._action_about.triggered.connect(self._on_action_about)
        self._action_preferences.triggered.connect(
            lambda: self.ui.statusBar().showMessage("Preferences — coming soon")
        )

        # ViewModel → View
        self._viewmodel.document_loaded.connect(self._on_document_loaded)
        self._viewmodel.encoding_detected.connect(self._on_encoding_detected)
        self._viewmodel.file_saved.connect(self._on_file_saved)
        self._viewmodel.error_occurred.connect(self._on_error)
        self._viewmodel.status_changed.connect(self._on_status_changed)

    # ---------------------------------------------------------- user actions

    def _on_tree_item_clicked(self, index: QModelIndex) -> None:
        """Load file on tree click; ignore directory clicks."""
        path = self._fs_model.filePath(index)
        if os.path.isfile(path):
            self._file_name_edit.setText(path)
            self._viewmodel.load_file(path)

    def _on_save_clicked(self) -> None:
        """Collect filepath and editor content, then delegate to ViewModel."""
        filepath = self._file_name_edit.text().strip()
        if not filepath:
            QMessageBox.warning(
                self.ui,
                "Save",
                "Enter a file path in the filename field before saving.",
            )
            return
        self._viewmodel.save_file(filepath, self._plain_text_edit.toPlainText())

    def _on_clean_requested(self) -> None:
        """Build CleaningOptions from checkbox states; delegate to ViewModel.

        Passes live editor text so user edits made since file-load are not lost.
        """
        options = CleaningOptions(
            trim_whitespace=self._trim_cb.isChecked(),
            clean_whitespace=self._clean_cb.isChecked(),
            remove_tabs=self._remove_tabs_cb.isChecked(),
        )
        self._viewmodel.apply_cleaning(options, self._plain_text_edit.toPlainText())

    def _on_find_clicked(self) -> None:
        """Find next occurrence of the search term in the editor."""
        term = self._find_edit.text()
        if not term:
            return
        found = self._plain_text_edit.find(term)
        if not found:
            # Wrap: move cursor to start and try again
            cursor = self._plain_text_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self._plain_text_edit.setTextCursor(cursor)
            self._plain_text_edit.find(term)

    def _on_replace_clicked(self) -> None:
        """Replace current selection if it matches, then find next."""
        find_term = self._find_edit.text()
        replace_term = self._replace_edit.text()
        if not find_term:
            return
        cursor = self._plain_text_edit.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == find_term:
            cursor.insertText(replace_term)
        self._on_find_clicked()

    def _on_replace_all_clicked(self) -> None:
        """Delegate replace-all to ViewModel, passing live editor text.

        Passes live editor text so user edits made since file-load are not lost.
        """
        self._viewmodel.replace_all(
            self._find_edit.text(),
            self._replace_edit.text(),
            self._plain_text_edit.toPlainText(),
        )

    def _on_action_open(self) -> None:
        """Open a file dialog and load the selected file."""
        path, _ = QFileDialog.getOpenFileName(
            self.ui,
            "Open File",
            QDir.homePath(),
            "Text Files (*.txt *.md *.csv *.log *.json *.yaml *.yml *.xml *.py *.sh *.conf *.ini *.toml);;All Files (*)",
        )
        if path:
            self._file_name_edit.setText(path)
            self._viewmodel.load_file(path)

    def _on_action_about(self) -> None:
        """Show an About dialog."""
        QMessageBox.about(
            self.ui,
            "About TextTools",
            "TextTools v0.2.0\n\nText processing utility: encoding detection, "
            "whitespace cleaning, find/replace, and file management.\n\n"
            "Built with Python 3.14 and PySide6.",
        )

    # ------------------------------------------ ViewModel signal handlers

    def _on_document_loaded(self, content: str) -> None:
        self._plain_text_edit.setPlainText(content)

    def _on_encoding_detected(self, encoding: str) -> None:
        self._encoding_label.setText(encoding)

    def _on_file_saved(self, filepath: str) -> None:
        self.ui.statusBar().showMessage(f"Saved: {filepath}")

    def _on_error(self, message: str) -> None:
        QMessageBox.critical(self.ui, "Error", message, QMessageBox.StandardButton.Ok)

    def _on_status_changed(self, message: str) -> None:
        self.ui.statusBar().showMessage(message)
