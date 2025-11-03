"""Main application window.

Views contain PySide6 UI components and minimal logic.
They observe ViewModels via signals and update UI accordingly.
UI is loaded from Qt Designer .ui files - NO hardcoded UI.
"""
import os
from PySide6.QtWidgets import QMainWindow, QPushButton, QListWidget, QTextEdit, QLabel, QMessageBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from src.viewmodels.main_viewmodel import MainViewModel


class MainWindow(QMainWindow):
    """Main application window.

    This view demonstrates:
    - Loading UI from Qt Designer .ui file
    - Clean separation from business logic
    - Signal/slot connections to ViewModel
    - Minimal UI-only logic
    """

    def __init__(self, viewmodel: MainViewModel):
        """Initialize the main window.

        Args:
            viewmodel: MainViewModel instance to bind to this view.
        """
        super().__init__()
        self._viewmodel = viewmodel

        self._load_ui()
        self._connect_signals()

    def _load_ui(self) -> None:
        """Load UI from Qt Designer .ui file.

        This replaces hardcoded UI construction.
        All layout, widgets, and properties are defined in the .ui file.
        """
        # Construct path to .ui file
        ui_file_path = os.path.join(
            os.path.dirname(__file__),
            'ui',
            'main_window.ui'
        )

        # Load the .ui file
        ui_file = QFile(ui_file_path)
        if not ui_file.open(QFile.ReadOnly):
            raise RuntimeError(f"Cannot open UI file: {ui_file_path}")

        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        # Set loaded UI as central widget
        self.setCentralWidget(self.ui)

        # Get references to widgets defined in .ui file
        # Widget names must match objectName in Qt Designer
        self._load_button = self.ui.findChild(QPushButton, "loadButton")
        self._clear_button = self.ui.findChild(QPushButton, "clearButton")
        self._list_widget = self.ui.findChild(QListWidget, "listWidget")
        self._details_text = self.ui.findChild(QTextEdit, "detailsText")
        self._status_label = self.ui.findChild(QLabel, "statusLabel")

    def _connect_signals(self) -> None:
        """Connect signals and slots.

        This is where the View binds to the ViewModel.
        - View signals (button clicks, etc.) trigger ViewModel methods
        - ViewModel signals trigger View update methods
        """
        # View to ViewModel (user actions)
        self._load_button.clicked.connect(self._viewmodel.load_data)
        self._clear_button.clicked.connect(self._viewmodel.clear_data)
        self._list_widget.currentRowChanged.connect(
            self._viewmodel.get_item_details
        )

        # ViewModel to View (state changes)
        self._viewmodel.data_loaded.connect(self._on_data_loaded)
        self._viewmodel.error_occurred.connect(self._on_error)
        self._viewmodel.status_changed.connect(self._on_status_changed)

    def _on_data_loaded(self, items: list) -> None:
        """Handle data loaded signal from ViewModel.

        Args:
            items: List of display strings to show.
        """
        self._list_widget.clear()
        self._list_widget.addItems(items)
        self._details_text.clear()

    def _on_error(self, message: str) -> None:
        """Handle error signal from ViewModel.

        Args:
            message: Error message to display.
        """
        QMessageBox.critical(
            self,
            "Error",
            message,
            QMessageBox.StandardButton.Ok
        )

    def _on_status_changed(self, status: str) -> None:
        """Handle status changed signal from ViewModel.

        Args:
            status: Status message to display.
        """
        self._status_label.setText(status)

        # If status is multiline, show in details view
        if '\n' in status:
            self._details_text.setPlainText(status)
