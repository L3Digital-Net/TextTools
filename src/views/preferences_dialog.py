"""PreferencesDialog — reads/writes QSettings for user-configurable editor preferences.

Deliberate MVVM exception: this dialog has no domain logic and no service calls.
It uses QSettings directly, matching the precedent in MainWindow._save_settings().
MainWindow connects preferences_changed to _apply_preferences() to apply settings live.

QSettings keys written here must stay in sync with MainWindow._apply_preferences().
"""

import os

from PySide6.QtCore import QDir, QFile, QObject, QSettings, Signal
from PySide6.QtGui import QFont
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFontComboBox,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QWidget,
)

from typing import TypeVar

_W = TypeVar("_W")


def _require(widget: "_W | None", name: str) -> "_W":
    if widget is None:
        raise RuntimeError(f"Required widget '{name}' not found in preferences_dialog.ui")
    return widget


# QSettings keys — must match MainWindow._apply_preferences() reads.
KEY_FONT_FAMILY = "editor/font_family"
KEY_FONT_SIZE = "editor/font_size"
KEY_WORD_WRAP = "editor/word_wrap"
KEY_LINE_NUMBERS = "editor/line_numbers"
KEY_THEME = "appearance/theme"
KEY_DEFAULT_DIR = "files/default_directory"

DEFAULTS = {
    KEY_FONT_FAMILY: "Monospace",
    KEY_FONT_SIZE: 12,
    KEY_WORD_WRAP: False,
    KEY_LINE_NUMBERS: True,
    KEY_THEME: "light",
    KEY_DEFAULT_DIR: QDir.homePath(),
}


class PreferencesDialog(QObject):
    """Preferences dialog controller.

    Loads preferences_dialog.ui, populates from QSettings, writes on Apply/OK.
    Emits preferences_changed after writing so MainWindow can apply settings live.

    self.dialog is the actual QDialog widget (the .ui root).
    """

    preferences_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._load_ui(parent)
        self._load_from_settings()
        self._connect_signals()

    def exec(self) -> int:
        """Show dialog modally. Returns QDialog.DialogCode."""
        return self.dialog.exec()

    # ------------------------------------------------------------------ setup

    def _load_ui(self, parent: QWidget | None) -> None:
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "preferences_dialog.ui")
        ui_file = QFile(ui_path)
        if not ui_file.open(QFile.OpenModeFlag.ReadOnly):
            raise RuntimeError(f"Cannot open UI file: {ui_path}")
        loader = QUiLoader()
        loaded = loader.load(ui_file, parent)
        ui_file.close()
        if loaded is None:
            raise RuntimeError("QUiLoader failed to load preferences_dialog.ui")
        self.dialog: QDialog = loaded  # type: ignore[assignment]

        self._font_family_combo = _require(
            self.dialog.findChild(QFontComboBox, "fontFamilyComboBox"),
            "fontFamilyComboBox",
        )
        self._font_size_spin = _require(
            self.dialog.findChild(QSpinBox, "fontSizeSpinBox"), "fontSizeSpinBox"
        )
        self._word_wrap_cb = _require(
            self.dialog.findChild(QCheckBox, "wordWrapCheckBox"), "wordWrapCheckBox"
        )
        self._line_numbers_cb = _require(
            self.dialog.findChild(QCheckBox, "lineNumbersCheckBox"), "lineNumbersCheckBox"
        )
        self._theme_light_radio = _require(
            self.dialog.findChild(QRadioButton, "themeLightRadio"), "themeLightRadio"
        )
        self._theme_dark_radio = _require(
            self.dialog.findChild(QRadioButton, "themeDarkRadio"), "themeDarkRadio"
        )
        self._default_dir_edit = _require(
            self.dialog.findChild(QLineEdit, "defaultDirectoryEdit"),
            "defaultDirectoryEdit",
        )
        self._browse_button = _require(
            self.dialog.findChild(QPushButton, "browseDirectoryButton"),
            "browseDirectoryButton",
        )
        self._ok_button = _require(
            self.dialog.findChild(QPushButton, "okButton"), "okButton"
        )
        self._apply_button = _require(
            self.dialog.findChild(QPushButton, "applyButton"), "applyButton"
        )
        self._cancel_button = _require(
            self.dialog.findChild(QPushButton, "cancelButton"), "cancelButton"
        )

    def _connect_signals(self) -> None:
        self._ok_button.clicked.connect(self._on_ok_clicked)
        self._apply_button.clicked.connect(self._on_apply_clicked)
        self._cancel_button.clicked.connect(self.dialog.reject)
        self._browse_button.clicked.connect(self._on_browse_clicked)

    # ------------------------------------------------------------------ logic

    def _load_from_settings(self) -> None:
        """Populate widgets from QSettings (falls back to DEFAULTS for missing keys)."""
        settings = QSettings()
        self._font_family_combo.setCurrentFont(
            QFont(str(settings.value(KEY_FONT_FAMILY, DEFAULTS[KEY_FONT_FAMILY])))
        )
        self._font_size_spin.setValue(
            int(settings.value(KEY_FONT_SIZE, DEFAULTS[KEY_FONT_SIZE]))
        )
        self._word_wrap_cb.setChecked(
            settings.value(KEY_WORD_WRAP, DEFAULTS[KEY_WORD_WRAP], type=bool)
        )
        self._line_numbers_cb.setChecked(
            settings.value(KEY_LINE_NUMBERS, DEFAULTS[KEY_LINE_NUMBERS], type=bool)
        )
        theme = settings.value(KEY_THEME, DEFAULTS[KEY_THEME])
        self._theme_dark_radio.setChecked(theme == "dark")
        self._theme_light_radio.setChecked(theme != "dark")
        self._default_dir_edit.setText(
            str(settings.value(KEY_DEFAULT_DIR, DEFAULTS[KEY_DEFAULT_DIR]))
        )

    def _write_to_settings(self) -> None:
        """Persist current widget values to QSettings."""
        settings = QSettings()
        settings.setValue(KEY_FONT_FAMILY, self._font_family_combo.currentFont().family())
        settings.setValue(KEY_FONT_SIZE, self._font_size_spin.value())
        settings.setValue(KEY_WORD_WRAP, self._word_wrap_cb.isChecked())
        settings.setValue(KEY_LINE_NUMBERS, self._line_numbers_cb.isChecked())
        settings.setValue(KEY_THEME, "dark" if self._theme_dark_radio.isChecked() else "light")
        settings.setValue(KEY_DEFAULT_DIR, self._default_dir_edit.text())

    def _on_apply_clicked(self) -> None:
        self._write_to_settings()
        self.preferences_changed.emit()

    def _on_ok_clicked(self) -> None:
        self._write_to_settings()
        self.preferences_changed.emit()
        self.dialog.accept()

    def _on_browse_clicked(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self.dialog,
            "Select Default Directory",
            self._default_dir_edit.text() or QDir.homePath(),
        )
        if path:
            self._default_dir_edit.setText(path)
