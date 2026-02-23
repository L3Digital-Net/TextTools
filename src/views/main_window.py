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

from PySide6.QtCore import QDir, QFile, QModelIndex, QSettings, Qt
from PySide6.QtGui import QAction, QColor, QFont, QKeySequence, QPalette, QShortcut
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QFileDialog,
    QFileSystemModel,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTreeView,
)

from src.models.cleaning_options import CleaningOptions
from src.utils.constants import APP_VERSION, TEXT_FILE_EXTENSIONS
from src.viewmodels.main_viewmodel import MainViewModel
from src.views.preferences_dialog import (
    DEFAULTS,
    KEY_DEFAULT_DIR,
    KEY_FONT_FAMILY,
    KEY_FONT_SIZE,
    KEY_LINE_NUMBERS,
    KEY_THEME,
    KEY_WORD_WRAP,
    PreferencesDialog,
)

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
        # Display-only filepath — ViewModel owns document state; this is for the title bar.
        self._filepath: str = ""
        self._load_ui()
        self._setup_file_tree()
        self._setup_merge_tab()
        self._connect_signals()
        self._load_settings()
        self._apply_preferences()
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._save_settings)

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
        # Tab widget — needed by focus-navigation shortcuts to reveal Find/Replace tab.
        self._tab_widget = _require(
            self.ui.findChild(QTabWidget, "tabWidget"), "tabWidget"
        )
        # Find/Replace is the last tab; cache its index so shortcuts stay correct
        # if tabs are reordered. Falls back to -1 (no-op) if tab is not found.
        self._find_replace_tab_index = next(
            (
                i
                for i in range(self._tab_widget.count())
                if self._tab_widget.tabText(i).lower().startswith("find")
            ),
            -1,
        )

        # Permanent status bar label — lives on the right, never overwritten by showMessage()
        self._cursor_label = QLabel("Ln 1, Col 1 | 0 chars")
        self.ui.statusBar().addPermanentWidget(self._cursor_label)

        self._main_splitter = _require(
            self.ui.findChild(QSplitter, "mainSplitter"), "mainSplitter"
        )
        # Merge tab widgets
        self._merge_file_list = _require(
            self.ui.findChild(QListWidget, "mergeFileList"), "mergeFileList"
        )
        self._merge_move_up_button = _require(
            self.ui.findChild(QPushButton, "mergeMoveUpButton"), "mergeMoveUpButton"
        )
        self._merge_move_down_button = _require(
            self.ui.findChild(QPushButton, "mergeMoveDownButton"), "mergeMoveDownButton"
        )
        self._merge_remove_button = _require(
            self.ui.findChild(QPushButton, "mergeRemoveButton"), "mergeRemoveButton"
        )
        self._merge_add_current_button = _require(
            self.ui.findChild(QPushButton, "mergeAddCurrentButton"),
            "mergeAddCurrentButton",
        )
        self._merge_add_files_button = _require(
            self.ui.findChild(QPushButton, "mergeAddFilesButton"), "mergeAddFilesButton"
        )
        self._merge_separator_edit = _require(
            self.ui.findChild(QLineEdit, "mergeSeparatorEdit"), "mergeSeparatorEdit"
        )
        self._merge_button = _require(
            self.ui.findChild(QPushButton, "mergeButton"), "mergeButton"
        )

    def _setup_file_tree(self) -> None:
        """Configure QFileSystemModel rooted at the user's home directory."""
        self._fs_model = QFileSystemModel(self.ui)
        self._fs_model.setRootPath(QDir.homePath())
        self._fs_model.setNameFilters(TEXT_FILE_EXTENSIONS)
        self._fs_model.setNameFilterDisables(False)  # hide non-matches (not just grey them)
        self._file_tree_view.setModel(self._fs_model)
        self._file_tree_view.setRootIndex(self._fs_model.index(QDir.homePath()))
        # Hide size/type/date columns — name column only
        for col in range(1, self._fs_model.columnCount()):
            self._file_tree_view.hideColumn(col)

    def _setup_merge_tab(self) -> None:
        """Configure the merge list widget (drag-drop mode set programmatically)."""
        self._merge_file_list.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove
        )
        self._merge_file_list.setDefaultDropAction(Qt.DropAction.MoveAction)

    def _connect_signals(self) -> None:
        """Wire UI events to ViewModel slots and ViewModel signals to UI handlers."""
        # Tab widget: resize to current tab's content height so shorter tabs
        # (Clean) don't show dead space reserved for taller tabs (Merge/Find).
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
        self._on_tab_changed(self._tab_widget.currentIndex())

        # File tree → load file (directories are filtered inside the slot)
        self._file_tree_view.clicked.connect(self._on_tree_item_clicked)

        # Save
        self._save_button.clicked.connect(self._on_save_clicked)

        # Cleaning: each checkbox triggers a fresh apply when a doc is loaded.
        # The checkboxes act as "apply now" toggles, not deferred configuration.
        # checkStateChanged replaces the deprecated stateChanged (Qt 6.7+); both
        # work but stateChanged passes int while checkStateChanged passes Qt.CheckState.
        # _on_clean_requested ignores the argument so either signature is compatible.
        self._trim_cb.checkStateChanged.connect(self._on_clean_requested)
        self._clean_cb.checkStateChanged.connect(self._on_clean_requested)
        self._remove_tabs_cb.checkStateChanged.connect(self._on_clean_requested)

        # Find / Replace
        self._find_button.clicked.connect(self._on_find_clicked)
        self._replace_button.clicked.connect(self._on_replace_clicked)
        self._replace_all_button.clicked.connect(self._on_replace_all_clicked)

        # Encoding conversion: pass live editor text so unsaved edits are preserved
        self._convert_button.clicked.connect(
            lambda: self._viewmodel.convert_to_utf8(self._plain_text_edit.toPlainText())
        )

        # Menu actions
        self._action_quit.triggered.connect(QApplication.quit)
        self._action_save.triggered.connect(self._on_save_clicked)
        self._action_open.triggered.connect(self._on_action_open)
        self._action_save_as.triggered.connect(self._on_action_save_as)
        self._action_about.triggered.connect(self._on_action_about)
        self._action_preferences.triggered.connect(self._on_action_preferences)

        # Merge tab
        self._merge_add_current_button.clicked.connect(
            self._viewmodel.add_current_to_merge
        )
        self._merge_add_files_button.clicked.connect(self._on_merge_add_files_clicked)
        self._merge_remove_button.clicked.connect(self._on_merge_remove_clicked)
        self._merge_move_up_button.clicked.connect(self._on_merge_move_up_clicked)
        self._merge_move_down_button.clicked.connect(self._on_merge_move_down_clicked)
        self._merge_separator_edit.textChanged.connect(
            self._viewmodel.set_merge_separator
        )
        self._merge_button.clicked.connect(self._viewmodel.execute_merge)
        # Drag-drop reorder: rowsMoved fires after an internal drag completes.
        # from_idx/to_idx are derived from start and destination_row of the move.
        self._merge_file_list.model().rowsMoved.connect(self._on_merge_rows_moved)

        # ViewModel → View
        self._viewmodel.document_loaded.connect(self._on_document_loaded)
        self._viewmodel.content_updated.connect(self._on_content_updated)
        self._viewmodel.encoding_detected.connect(self._on_encoding_detected)
        self._viewmodel.file_saved.connect(self._on_file_saved)
        self._viewmodel.error_occurred.connect(self._on_error)
        self._viewmodel.status_changed.connect(self._on_status_changed)
        self._viewmodel.merge_list_changed.connect(self._on_merge_list_changed)

        # Title bar: modificationChanged fires only when isModified() flips, not on
        # every keystroke — avoids redundant title repaints and gives a clean signal.
        self._plain_text_edit.document().modificationChanged.connect(
            lambda _: self._update_title()
        )

        # Cursor position: update permanent label on every cursor move
        self._plain_text_edit.cursorPositionChanged.connect(self._update_cursor_label)
        # contentsChanged fires on Delete/Backspace where cursor position does not
        # change — without this the char count goes stale after in-place deletions.
        self._plain_text_edit.document().contentsChanged.connect(self._update_cursor_label)

        # Keyboard shortcuts not present in the .ui file.
        # (Ctrl+S/O/Q/Shift+S are already wired via QAction shortcuts in main_window.ui.)
        # ApplicationShortcut context: fires even when a child widget holds focus,
        # rather than requiring the window itself to be active. Necessary for focus
        # navigation shortcuts that must work regardless of which widget is focused.
        ctrl_f = QShortcut(QKeySequence("Ctrl+F"), self.ui)
        ctrl_f.setContext(Qt.ShortcutContext.ApplicationShortcut)
        ctrl_f.activated.connect(self._focus_find_edit)

        ctrl_h = QShortcut(QKeySequence("Ctrl+H"), self.ui)
        ctrl_h.setContext(Qt.ShortcutContext.ApplicationShortcut)
        ctrl_h.activated.connect(self._focus_replace_edit)

        f3 = QShortcut(QKeySequence("F3"), self.ui)
        f3.setContext(Qt.ShortcutContext.ApplicationShortcut)
        f3.activated.connect(self._on_find_clicked)

    # ---------------------------------------------------------- user actions

    def _on_tab_changed(self, index: int) -> None:
        """Cap tab widget height to the current page's content.

        QTabWidget internally uses QStackedWidget whose sizeHint() always
        returns the max of ALL children — ignoring per-page size policies.
        setMaximumHeight is the only reliable way to shrink the widget for
        shorter pages (Clean tab) while letting taller pages expand.
        """
        page = self._tab_widget.widget(index)
        if page is None:
            return
        tab_bar_h = self._tab_widget.tabBar().sizeHint().height()
        page_h = page.sizeHint().height()
        self._tab_widget.setMaximumHeight(tab_bar_h + page_h)

    def _focus_find_edit(self) -> None:
        """Switch to Find/Replace tab and focus the find field (Ctrl+F target)."""
        if self._find_replace_tab_index >= 0:
            self._tab_widget.setCurrentIndex(self._find_replace_tab_index)
        self._find_edit.setFocus()

    def _focus_replace_edit(self) -> None:
        """Switch to Find/Replace tab and focus the replace field (Ctrl+H target)."""
        if self._find_replace_tab_index >= 0:
            self._tab_widget.setCurrentIndex(self._find_replace_tab_index)
        self._replace_edit.setFocus()

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
        _glob = " ".join(TEXT_FILE_EXTENSIONS)
        path, _ = QFileDialog.getOpenFileName(
            self.ui,
            "Open File",
            QDir.homePath(),
            f"Text Files ({_glob});;All Files (*)",
        )
        if path:
            self._file_name_edit.setText(path)
            self._viewmodel.load_file(path)

    def _on_action_save_as(self) -> None:
        """Open a Save As dialog; save to the chosen path if confirmed."""
        _glob = " ".join(TEXT_FILE_EXTENSIONS)
        initial = self._file_name_edit.text() or QDir.homePath()
        path, _ = QFileDialog.getSaveFileName(
            self.ui,
            "Save As",
            initial,
            f"Text Files ({_glob});;All Files (*)",
        )
        if path:
            self._file_name_edit.setText(path)
            self._on_save_clicked()

    def _on_action_about(self) -> None:
        """Show an About dialog."""
        QMessageBox.about(
            self.ui,
            "About TextTools",
            f"TextTools v{APP_VERSION}\n\nText processing utility: encoding detection, "
            "whitespace cleaning, find/replace, and file management.\n\n"
            "Built with Python 3.14 and PySide6.",
        )

    def _on_action_preferences(self) -> None:
        """Open the Preferences dialog; apply settings after dialog closes.

        Preferences are applied once after exec() returns rather than live via
        preferences_changed signal. Connecting _apply_preferences during exec()
        causes app.setPalette() + setRootIndex() to trigger recursive repaints
        inside the modal event loop → SIGSEGV. Cancel leaves QSettings unchanged
        so _apply_preferences() is a no-op after Cancel.
        """
        prefs = PreferencesDialog(self.ui)
        prefs.exec()
        self._apply_preferences()

    # ---------------------------------------------------------- merge tab handlers

    def _on_merge_add_files_clicked(self) -> None:
        """Open a multi-select file dialog and add chosen files to the merge list."""
        paths, _ = QFileDialog.getOpenFileNames(
            self.ui, "Add Files to Merge", QDir.homePath()
        )
        if paths:
            self._viewmodel.add_files_to_merge(paths)

    def _on_merge_remove_clicked(self) -> None:
        """Remove the currently selected item from the merge list."""
        row = self._merge_file_list.currentRow()
        if row >= 0:
            self._viewmodel.remove_from_merge(row)

    def _on_merge_move_up_clicked(self) -> None:
        """Move the selected merge item one position earlier."""
        row = self._merge_file_list.currentRow()
        if row > 0:
            self._viewmodel.move_merge_item(row, row - 1)
            self._merge_file_list.setCurrentRow(row - 1)

    def _on_merge_move_down_clicked(self) -> None:
        """Move the selected merge item one position later."""
        row = self._merge_file_list.currentRow()
        if row >= 0 and row < self._merge_file_list.count() - 1:
            self._viewmodel.move_merge_item(row, row + 2)
            self._merge_file_list.setCurrentRow(row + 1)

    def _on_merge_rows_moved(
        self,
        _parent: object,
        start: int,
        _end: int,
        _dest_parent: object,
        dest_row: int,
    ) -> None:
        """Sync a drag-drop reorder in mergeFileList to the ViewModel."""
        self._viewmodel.move_merge_item(start, dest_row)

    # ---------------------------------------------------------- title-bar helpers

    def _set_editor_text(self, content: str) -> None:
        """Replace editor content as a single undoable operation.

        Uses QTextCursor.insertText instead of setPlainText to preserve the undo
        stack — setPlainText resets it entirely.
        """
        cursor = self._plain_text_edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        cursor.insertText(content)

    def _update_title(self) -> None:
        """Reflect current filepath and modified state in the window title."""
        name = os.path.basename(self._filepath) if self._filepath else ""
        modified = self._plain_text_edit.document().isModified()
        suffix = " *" if modified else ""
        self.ui.setWindowTitle(f"TextTools — {name}{suffix}" if name else "TextTools")

    def _update_cursor_label(self) -> None:
        """Update the permanent cursor position label in the status bar."""
        cursor = self._plain_text_edit.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        # document().characterCount() includes one trailing paragraph separator;
        # subtract 1 to report the user-visible character count.
        # 190x faster than toPlainText() — avoids a full string allocation per keypress.
        chars = self._plain_text_edit.document().characterCount() - 1
        self._cursor_label.setText(f"Ln {line}, Col {col} | {chars:,} chars")

    def _load_settings(self) -> None:
        """Restore window geometry and splitter positions from QSettings.

        Silent no-op when no settings exist yet (first launch or cleared).
        """
        # QSettings() (zero-arg) resolves org/app from QCoreApplication identity
        # set in main() — avoids silent divergence if APP_NAME is ever renamed.
        settings = QSettings()
        if geometry := settings.value("window/geometry"):
            self.ui.restoreGeometry(geometry)
        if main_state := settings.value("splitter/main"):
            self._main_splitter.restoreState(main_state)

    def _save_settings(self) -> None:
        """Save window geometry and splitter positions to QSettings.

        Connected to QApplication.aboutToQuit in __init__.
        """
        settings = QSettings()
        settings.setValue("window/geometry", self.ui.saveGeometry())
        settings.setValue("splitter/main", self._main_splitter.saveState())

    def _apply_preferences(self) -> None:
        """Apply user preferences from QSettings to the editor.

        Called once on startup (after _load_settings) and whenever
        PreferencesDialog emits preferences_changed — keeps the editor live.
        QSettings keys read here must stay in sync with preferences_dialog.py.
        """
        settings = QSettings()

        # Font
        family = str(settings.value(KEY_FONT_FAMILY, DEFAULTS[KEY_FONT_FAMILY]))
        size = int(settings.value(KEY_FONT_SIZE, DEFAULTS[KEY_FONT_SIZE]))
        self._plain_text_edit.setFont(QFont(family, size))

        # Word wrap
        wrap = settings.value(KEY_WORD_WRAP, DEFAULTS[KEY_WORD_WRAP], type=bool)
        self._plain_text_edit.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.WidgetWidth
            if wrap
            else QPlainTextEdit.LineWrapMode.NoWrap
        )

        # Theme — Fusion style with a dark palette; restore system default for light.
        theme = str(settings.value(KEY_THEME, DEFAULTS[KEY_THEME]))
        app = QApplication.instance()
        if app is not None:
            if theme == "dark":
                app.setStyle("Fusion")
                palette = QPalette()
                palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
                palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
                palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
                palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
                palette.setColor(
                    QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black
                )
                app.setPalette(palette)
            else:
                app.setPalette(QPalette())  # restore system default

        # Default directory — update file tree root to user's preferred start location.
        default_dir = str(settings.value(KEY_DEFAULT_DIR, DEFAULTS[KEY_DEFAULT_DIR]))
        if os.path.isdir(default_dir):
            self._fs_model.setRootPath(default_dir)
            self._file_tree_view.setRootIndex(self._fs_model.index(default_dir))

        # Line numbers: stored in QSettings; rendering deferred (LineNumberEditor
        # requires a custom QPlainTextEdit subclass — separate follow-on task).
        _ = settings.value(KEY_LINE_NUMBERS, DEFAULTS[KEY_LINE_NUMBERS], type=bool)

    # ------------------------------------------ ViewModel signal handlers

    def _on_document_loaded(self, content: str) -> None:
        self._set_editor_text(content)
        self._plain_text_edit.document().setModified(False)
        # fileNameEdit is always populated before load_file is called (see
        # _on_tree_item_clicked and _on_action_open). Reading the widget here
        # keeps the View in its own layer — never access ViewModel private state.
        self._filepath = self._file_name_edit.text()
        self._update_title()

    def _on_content_updated(self, content: str) -> None:
        """Handle in-place text transformation (cleaning, replace-all).

        Does NOT clear the modified flag or update _filepath — content was
        transformed, not loaded fresh from disk.
        """
        self._set_editor_text(content)

    def _on_encoding_detected(self, encoding: str) -> None:
        self._encoding_label.setText(encoding)

    def _on_file_saved(self, filepath: str) -> None:
        self._filepath = filepath
        self._plain_text_edit.document().setModified(False)
        self.ui.statusBar().showMessage(f"Saved: {filepath}")
        self._update_title()

    def _on_error(self, message: str) -> None:
        QMessageBox.critical(self.ui, "Error", message, QMessageBox.StandardButton.Ok)

    def _on_status_changed(self, message: str) -> None:
        self.ui.statusBar().showMessage(message)

    def _on_merge_list_changed(self, names: list[str]) -> None:
        """Repopulate mergeFileList from the ViewModel's display-name list."""
        self._merge_file_list.clear()
        self._merge_file_list.addItems(names)
