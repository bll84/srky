"""Main application window."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.device_discovery_panel import DeviceDiscoveryPanel
from app.ui.device_detail_panel import DeviceDetailPanel
from app.ui.test_center_panel import TestCenterPanel
from app.ui.pin_matrix_panel import PinMatrixPanel
from app.ui.report_panel import ReportPanel
from app.ui.styles import STYLESHEET

if TYPE_CHECKING:
    from app.controllers.app_controller import AppController

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""

    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("DeviceProbe - Çoklu Cihaz Test Platformu")
        self.setMinimumSize(QSize(1100, 700))
        self.resize(1280, 800)
        self.setStyleSheet(STYLESHEET)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(56)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 16, 8)

        title = QLabel("DeviceProbe")
        title.setObjectName("title")
        header_layout.addWidget(title)

        subtitle = QLabel("Çoklu Cihaz Tanıma ve Test Platformu")
        subtitle.setObjectName("subtitle")
        header_layout.addWidget(subtitle)
        header_layout.addStretch()

        self.status_label = QLabel("Hazır")
        self.status_label.setObjectName("subtitle")
        header_layout.addWidget(self.status_label)

        main_layout.addWidget(header)

        # Splitter: left (discovery) + right (tabs)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Discovery
        self.discovery_panel = DeviceDiscoveryPanel(self.controller)
        splitter.addWidget(self.discovery_panel)

        # Right panel: Tabs
        self.tabs = QTabWidget()
        self.detail_panel = DeviceDetailPanel(self.controller)
        self.test_center = TestCenterPanel(self.controller)
        self.pin_matrix = PinMatrixPanel(self.controller)
        self.report_panel = ReportPanel(self.controller)

        self.tabs.addTab(self.detail_panel, "Cihaz Detayı")
        self.tabs.addTab(self.test_center, "Test Merkezi")
        self.tabs.addTab(self.pin_matrix, "Pin Haritası")
        self.tabs.addTab(self.report_panel, "Raporlar")

        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

        # Status bar
        self.statusBar().showMessage("DeviceProbe v1.0 - Cihaz seçilmedi")

    def _connect_signals(self) -> None:
        self.controller.status_changed.connect(self._on_status)
        self.controller.device_selected.connect(self._on_device_selected)

    def _on_status(self, msg: str) -> None:
        self.status_label.setText(msg)
        self.statusBar().showMessage(msg)

    def _on_device_selected(self, device_id: str) -> None:
        self.detail_panel.refresh(device_id)
        self.test_center.refresh(device_id)
        self.pin_matrix.refresh(device_id)

    def closeEvent(self, event) -> None:
        self.controller.shutdown()
        super().closeEvent(event)
