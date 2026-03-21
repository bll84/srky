"""Report viewing and export panel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.report_engine.reporter import ReportEngine

if TYPE_CHECKING:
    from app.controllers.app_controller import AppController


class ReportPanel(QWidget):
    """Panel for viewing and exporting test reports."""

    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.controller = controller
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("Test Reports")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Controls
        ctrl_layout = QHBoxLayout()

        self.format_combo = QComboBox()
        self.format_combo.addItems(["Text", "JSON", "CSV"])
        self.format_combo.currentTextChanged.connect(self._refresh_view)
        ctrl_layout.addWidget(QLabel("Format:"))
        ctrl_layout.addWidget(self.format_combo)
        ctrl_layout.addStretch()

        self.export_btn = QPushButton("Export Report")
        self.export_btn.clicked.connect(self._export)
        self.export_btn.setEnabled(False)
        ctrl_layout.addWidget(self.export_btn)

        layout.addLayout(ctrl_layout)

        # Report view
        report_group = QGroupBox("Report Content")
        report_layout = QVBoxLayout(report_group)
        self.report_text = QPlainTextEdit()
        self.report_text.setReadOnly(True)
        report_layout.addWidget(self.report_text)
        layout.addWidget(report_group)

        # Summary
        self.summary_label = QLabel("No report available. Run tests first.")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

    def _connect_signals(self) -> None:
        self.controller.report_ready.connect(self._on_report)

    def _on_report(self) -> None:
        self.export_btn.setEnabled(True)
        self._refresh_view()

    def _refresh_view(self) -> None:
        report = self.controller.get_last_report()
        if not report:
            return

        fmt = self.format_combo.currentText()
        if fmt == "JSON":
            text = ReportEngine.to_json(report)
        elif fmt == "CSV":
            text = ReportEngine.to_csv(report)
        else:
            text = ReportEngine.to_text(report)

        self.report_text.setPlainText(text)
        self.summary_label.setText(
            f"Device: {report.board_model} | "
            f"Total: {report.total_tests} | "
            f"Pass: {report.passed} | Fail: {report.failed} | "
            f"Warn: {report.warnings} | Skip: {report.skipped}"
        )

    def _export(self) -> None:
        report = self.controller.get_last_report()
        if not report:
            return

        fmt = self.format_combo.currentText()
        ext_map = {"Text": "txt", "JSON": "json", "CSV": "csv"}
        ext = ext_map.get(fmt, "txt")

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Report",
            f"report_{report.board_model.replace(' ', '_')}.{ext}",
            f"{fmt} Files (*.{ext})",
        )
        if path:
            if fmt == "JSON":
                ReportEngine.save_json(report, path)
            elif fmt == "CSV":
                ReportEngine.save_csv(report, path)
            else:
                ReportEngine.save_text(report, path)
