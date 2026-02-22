#!/usr/bin/env python
"""Offscreen smoke test for TextTools.

Exercises the full stack (FileService → ViewModel → View widgets) using Qt's
offscreen platform — no display or Xvfb required.

Run with:
    uv run python scripts/live_test.py

Exit code: 0 if all checks pass, 1 if any fail.

QT_QPA_PLATFORM=offscreen: renders widgets in memory; all Qt geometry, text
cursor, and signal APIs work identically to a real display, but nothing is
shown on screen. More stable than Xvfb for headless testing because there is
no input method context to trip over.
"""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Must be set before QApplication is created — do not move below imports.
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QT_IM_MODULE"] = "none"

# Add project root to sys.path so `src` is importable without install.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from src.main import create_application  # noqa: E402

_pass = 0
_fail = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global _pass, _fail
    if condition:
        print(f"  PASS  {label}")
        _pass += 1
    else:
        note = f" — {detail}" if detail else ""
        print(f"  FAIL  {label}{note}")
        _fail += 1


def section(title: str) -> None:
    print(f"\n{title}")
    print("─" * len(title))


def main() -> None:
    app = QApplication(sys.argv)
    window = create_application()

    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # ----------------------------------------------------------------- load
        section("File Loading")

        # Non-ASCII content (é, ñ) is required for the encoding check:
        # pure ASCII is correctly detected as "ascii" by chardet (ASCII ⊂ UTF-8).
        f = tmp_path / "hello.txt"
        f.write_text("café résumé — live test", encoding="utf-8")
        window._file_name_edit.setText(str(f))
        window._viewmodel.load_file(str(f))
        app.processEvents()

        check(
            "Editor populated after load",
            window._plain_text_edit.toPlainText() == "café résumé — live test",
        )
        check(
            "Encoding label shows utf-8",
            window._encoding_label.text().lower() == "utf-8",
        )
        check(
            "Title bar shows filename",
            "hello.txt" in window.ui.windowTitle(),
        )
        check(
            "Title bar has no star (clean after load)",
            "*" not in window.ui.windowTitle(),
        )
        check(
            "Status bar mentions filename",
            "hello.txt" in window.ui.statusBar().currentMessage(),
        )

        # ----------------------------------------------------------------- save
        section("Save")

        out = tmp_path / "out.txt"
        window._file_name_edit.setText(str(out))
        window._plain_text_edit.setPlainText("saved content")
        window._on_save_clicked()
        app.processEvents()

        check(
            "File written to disk",
            out.exists(),
        )
        check(
            "File content matches editor",
            out.exists() and out.read_text(encoding="utf-8") == "saved content",
        )
        check(
            "Title loses star after save",
            "*" not in window.ui.windowTitle(),
        )

        # -------------------------------------------------------------- cleaning
        section("Text Cleaning (real TextProcessingService)")

        dirty = tmp_path / "dirty.txt"
        dirty.write_text("hello   \nworld   \n\n", encoding="utf-8")
        window._file_name_edit.setText(str(dirty))
        window._viewmodel.load_file(str(dirty))
        app.processEvents()

        window._trim_cb.setChecked(True)
        app.processEvents()

        trimmed = window._plain_text_edit.toPlainText()
        check(
            "Trim whitespace strips trailing spaces and blank lines",
            trimmed == "hello\nworld",
            f"got: {trimmed!r}",
        )

        window._trim_cb.setChecked(False)
        app.processEvents()

        # Reload clean content for the next two checks
        spaces = tmp_path / "spaces.txt"
        spaces.write_text("a  b   c", encoding="utf-8")
        window._file_name_edit.setText(str(spaces))
        window._viewmodel.load_file(str(spaces))
        app.processEvents()

        window._clean_cb.setChecked(True)
        app.processEvents()

        collapsed = window._plain_text_edit.toPlainText()
        check(
            "Clean whitespace collapses runs of spaces",
            collapsed == "a b c",
            f"got: {collapsed!r}",
        )

        window._clean_cb.setChecked(False)
        app.processEvents()

        tabs_file = tmp_path / "tabs.txt"
        tabs_file.write_text("\tindented\n\t\tdouble", encoding="utf-8")
        window._file_name_edit.setText(str(tabs_file))
        window._viewmodel.load_file(str(tabs_file))
        app.processEvents()

        window._remove_tabs_cb.setChecked(True)
        app.processEvents()

        detabbed = window._plain_text_edit.toPlainText()
        check(
            "Remove tabs strips leading indent",
            detabbed == "indented\ndouble",
            f"got: {detabbed!r}",
        )

        window._remove_tabs_cb.setChecked(False)
        app.processEvents()

        # --------------------------------------------------------------- find
        section("Find")

        search = tmp_path / "search.txt"
        search.write_text("the quick brown fox", encoding="utf-8")
        window._file_name_edit.setText(str(search))
        window._viewmodel.load_file(str(search))
        app.processEvents()

        window._find_edit.setText("brown")
        window._on_find_clicked()
        selected = window._plain_text_edit.textCursor().selectedText()
        check(
            "Find selects matching text",
            selected == "brown",
            f"got: {selected!r}",
        )

        # Wrap test: move cursor to end, search for earlier word
        cursor = window._plain_text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        window._plain_text_edit.setTextCursor(cursor)
        window._find_edit.setText("quick")
        window._on_find_clicked()
        selected = window._plain_text_edit.textCursor().selectedText()
        check(
            "Find wraps from end of document",
            selected == "quick",
            f"got: {selected!r}",
        )

        # --------------------------------------------------------- replace all
        section("Replace All")

        rep = tmp_path / "rep.txt"
        rep.write_text("cat cat cat", encoding="utf-8")
        window._file_name_edit.setText(str(rep))
        window._viewmodel.load_file(str(rep))
        app.processEvents()

        window._find_edit.setText("cat")
        window._replace_edit.setText("dog")
        window._on_replace_all_clicked()
        app.processEvents()

        result = window._plain_text_edit.toPlainText()
        check(
            "Replace All updates all occurrences",
            result == "dog dog dog",
            f"got: {result!r}",
        )

        # --------------------------------------------------------------- stubs
        section("Stub Actions")

        window._convert_button.click()
        app.processEvents()
        check(
            "Convert shows coming-soon status",
            "coming soon" in window.ui.statusBar().currentMessage().lower(),
        )

    # ----------------------------------------------------------------------- summary
    total = _pass + _fail
    print(f"\n{'=' * 42}")
    if _fail == 0:
        print(f"All {total} checks passed.")
    else:
        print(f"{_pass}/{total} passed — {_fail} FAILED.")
    print("=" * 42)

    window.ui.close()
    app.quit()
    sys.exit(1 if _fail else 0)


if __name__ == "__main__":
    main()
