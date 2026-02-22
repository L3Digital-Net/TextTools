"""Unit tests for PreferencesDialog — QSettings reads/writes.

Tests redirect QSettings to a tmp ini file (via monkeypatch) so they never
touch real user preferences.  The dialog is exercised without calling exec()
so no event loops are needed.
"""

import pytest
from PySide6.QtCore import QSettings


@pytest.fixture
def isolated_settings(tmp_path, monkeypatch):
    """Patch src.views.preferences_dialog.QSettings to use a temp ini file.

    Returns the ini path so test bodies can pre-set values or verify writes
    via QSettings(returned_path, IniFormat) — the same backing file the
    dialog uses.
    """
    tmp_ini = str(tmp_path / "prefs_test.ini")
    monkeypatch.setattr(
        "src.views.preferences_dialog.QSettings",
        lambda *_: QSettings(tmp_ini, QSettings.Format.IniFormat),
    )
    return tmp_ini


@pytest.fixture
def dialog(isolated_settings, qapp):
    """Construct PreferencesDialog with isolated settings (no user prefs touched)."""
    from src.views.preferences_dialog import PreferencesDialog

    return PreferencesDialog()


class TestLoadFromSettings:
    def test_defaults_shown_when_no_settings(self, dialog):
        """Empty QSettings → widgets reflect DEFAULTS."""
        from src.views.preferences_dialog import DEFAULTS, KEY_FONT_SIZE

        assert dialog._font_size_spin.value() == DEFAULTS[KEY_FONT_SIZE]
        assert dialog._theme_light_radio.isChecked()
        assert not dialog._word_wrap_cb.isChecked()

    def test_loads_font_size_from_settings(self, isolated_settings, qapp):
        """Font size spinbox reflects stored value on dialog init."""
        from src.views.preferences_dialog import KEY_FONT_SIZE, PreferencesDialog

        QSettings(isolated_settings, QSettings.Format.IniFormat).setValue(
            KEY_FONT_SIZE, 18
        )
        dlg = PreferencesDialog()
        assert dlg._font_size_spin.value() == 18

    def test_loads_dark_theme_from_settings(self, isolated_settings, qapp):
        """Dark radio is checked when KEY_THEME is 'dark'."""
        from src.views.preferences_dialog import KEY_THEME, PreferencesDialog

        QSettings(isolated_settings, QSettings.Format.IniFormat).setValue(
            KEY_THEME, "dark"
        )
        dlg = PreferencesDialog()
        assert dlg._theme_dark_radio.isChecked()
        assert not dlg._theme_light_radio.isChecked()

    def test_loads_word_wrap_from_settings(self, isolated_settings, qapp):
        """Word wrap checkbox reflects stored boolean."""
        from src.views.preferences_dialog import KEY_WORD_WRAP, PreferencesDialog

        QSettings(isolated_settings, QSettings.Format.IniFormat).setValue(
            KEY_WORD_WRAP, True
        )
        dlg = PreferencesDialog()
        assert dlg._word_wrap_cb.isChecked()


class TestWriteToSettings:
    def test_apply_writes_font_size(self, dialog, isolated_settings):
        """Clicking Apply persists font_size to QSettings."""
        from src.views.preferences_dialog import KEY_FONT_SIZE

        dialog._font_size_spin.setValue(24)
        dialog._apply_button.click()
        s = QSettings(isolated_settings, QSettings.Format.IniFormat)
        assert int(s.value(KEY_FONT_SIZE)) == 24

    def test_apply_writes_theme_dark(self, dialog, isolated_settings):
        """Clicking Apply persists 'dark' when dark radio is selected."""
        from src.views.preferences_dialog import KEY_THEME

        dialog._theme_dark_radio.setChecked(True)
        dialog._apply_button.click()
        s = QSettings(isolated_settings, QSettings.Format.IniFormat)
        assert s.value(KEY_THEME) == "dark"

    def test_apply_writes_word_wrap(self, dialog, isolated_settings):
        """Clicking Apply persists word_wrap boolean."""
        from src.views.preferences_dialog import KEY_WORD_WRAP

        dialog._word_wrap_cb.setChecked(True)
        dialog._apply_button.click()
        s = QSettings(isolated_settings, QSettings.Format.IniFormat)
        assert s.value(KEY_WORD_WRAP, type=bool) is True

    def test_ok_writes_settings(self, dialog, isolated_settings):
        """_on_ok_clicked writes settings before accepting."""
        from src.views.preferences_dialog import KEY_FONT_SIZE

        dialog._font_size_spin.setValue(16)
        dialog._on_ok_clicked()  # writes + emits + accepts (safe on non-shown dialog)
        s = QSettings(isolated_settings, QSettings.Format.IniFormat)
        assert int(s.value(KEY_FONT_SIZE)) == 16

    def test_cancel_does_not_write_settings(self, dialog, isolated_settings):
        """Clicking Cancel does not persist any widget changes."""
        from src.views.preferences_dialog import KEY_FONT_SIZE

        dialog._font_size_spin.setValue(99)
        dialog._cancel_button.click()
        s = QSettings(isolated_settings, QSettings.Format.IniFormat)
        # Nothing was written — key absent means cancel left settings untouched.
        assert s.value(KEY_FONT_SIZE) is None


class TestSignals:
    def test_apply_emits_preferences_changed(self, dialog, qtbot):
        """preferences_changed is emitted when Apply is clicked."""
        with qtbot.waitSignal(dialog.preferences_changed, timeout=1000):
            dialog._apply_button.click()

    def test_ok_emits_preferences_changed(self, dialog, qtbot):
        """preferences_changed is emitted when OK is clicked."""
        with qtbot.waitSignal(dialog.preferences_changed, timeout=1000):
            dialog._on_ok_clicked()
