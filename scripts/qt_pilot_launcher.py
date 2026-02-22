"""Qt-pilot test launcher — sets QT_IM_MODULE=none before QApplication is created.

Without this, QTest::keyClicks causes a SIGSEGV on headless displays (Xvfb, etc.)
because there is no input method context. Setting QT_IM_MODULE=none disables the
input method plugin lookup and prevents the null-pointer dereference.

Use with the qt-pilot MCP tool:
    launch_app(
        script_path="scripts/qt_pilot_launcher.py",
        working_dir="/home/chris/projects/TextTools",
        python_paths=["/home/chris/projects/TextTools"],
    )
"""

import os

# Must be set before QApplication is created — do not move below imports.
os.environ.setdefault("QT_IM_MODULE", "none")

from src.main import main  # noqa: E402

if __name__ == "__main__":
    main()
