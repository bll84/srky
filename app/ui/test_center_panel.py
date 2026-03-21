"""Test center panel for running tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from app.controllers.app_controller import AppController
    from core.models import TestReport


class TestWorker(QThread):
    """Worker thread for running tests."""
    progress = Signal(str, int, int)  # test_id, current, total
    finished = Signal(object)  # TestReport

    def __init__(self, controller, device_id: str, mode: str) -> None:
        super().__init__()
        self.controller = controller
        self.device_id = device_id
        self.mode = mode

    def run(self) -> None:
        report = self.controller.run_tests(
            self.device_id, self.mode,
            progress_callback=self.progress.emit,
        )
        self.finished.emit(report)


class TestCenterPanel(QWidget):
    """Panel for running and monitoring device tests."""

    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.controller = controller
        self._current_device_id: str = ""
        self._worker: TestWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("Test Merkezi")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.device_label = QLabel("Cihaz seçilmedi")
        layout.addWidget(self.device_label)

        # Test butonları
        btn_group = QGroupBox("Testleri Çalıştır")
        btn_layout = QHBoxLayout(btn_group)

        self.quick_btn = QPushButton("Hızlı Test")
        self.quick_btn.setObjectName("primaryBtn")
        self.quick_btn.clicked.connect(lambda: self._run_test("quick"))
        self.quick_btn.setEnabled(False)
        btn_layout.addWidget(self.quick_btn)

        self.full_btn = QPushButton("Tam Test")
        self.full_btn.clicked.connect(lambda: self._run_test("full"))
        self.full_btn.setEnabled(False)
        btn_layout.addWidget(self.full_btn)

        self.stop_btn = QPushButton("Durdur")
        self.stop_btn.setObjectName("dangerBtn")
        self.stop_btn.clicked.connect(self._stop_test)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        layout.addWidget(btn_group)

        # İlerleme
        progress_group = QGroupBox("İlerleme")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("Bekliyor")
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(progress_group)

        # Sonuçlar
        self.results_group = QGroupBox("Sonuçlar")
        results_layout = QVBoxLayout(self.results_group)
        self.results_text = QPlainTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        layout.addWidget(self.results_group)

        # Güvenlik uyarısı
        warning = QLabel(
            "Not: Yazılımsal testler firmware seviyesindeki yanıtları doğrular. "
            "Fiziksel pin sağlamlığı için jumper kablo ile loopback testi gereklidir. "
            "Rezerve/boot pinleri güvenlik için atlanır."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #fab387; font-size: 11px; padding: 8px;")
        layout.addWidget(warning)

    def refresh(self, device_id: str) -> None:
        self._current_device_id = device_id
        device = self.controller.get_device(device_id)
        if device:
            connected = self.controller.is_connected(device_id)
            self.device_label.setText(
                f"Cihaz: {device.board_model} | "
                f"{'Bağlı' if connected else 'Bağlı değil'}"
            )
            self.quick_btn.setEnabled(connected)
            self.full_btn.setEnabled(connected)
        else:
            self.device_label.setText("Cihaz seçilmedi")
            self.quick_btn.setEnabled(False)
            self.full_btn.setEnabled(False)

    def _run_test(self, mode: str) -> None:
        if not self._current_device_id:
            return

        self.quick_btn.setEnabled(False)
        self.full_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.results_text.clear()

        self._worker = TestWorker(self.controller, self._current_device_id, mode)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _stop_test(self) -> None:
        self.controller.stop_tests()
        self.stop_btn.setEnabled(False)
        self.progress_label.setText("Durduruluyor...")

    def _on_progress(self, test_id: str, current: int, total: int) -> None:
        pct = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.progress_label.setText(f"Çalışıyor: {test_id} ({current}/{total})")

    def _on_finished(self, report) -> None:
        self.stop_btn.setEnabled(False)
        self.quick_btn.setEnabled(True)
        self.full_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.progress_label.setText("Tamamlandı")

        if report:
            from core.report_engine.reporter import ReportEngine
            text = ReportEngine.to_text(report)
            self.results_text.setPlainText(text)
            self.controller.set_last_report(report)
