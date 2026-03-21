"""Pin matrix visualization panel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.models import PinFunction, PinStatus

if TYPE_CHECKING:
    from app.controllers.app_controller import AppController

STATUS_COLORS = {
    PinStatus.AVAILABLE: "#a6e3a1",
    PinStatus.RESERVED: "#fab387",
    PinStatus.WARNING: "#f9e2af",
    PinStatus.PASSED: "#a6e3a1",
    PinStatus.FAILED: "#f38ba8",
    PinStatus.UNSUPPORTED: "#585b70",
    PinStatus.UNTESTED: "#6c7086",
}


class PinMatrixPanel(QWidget):
    """Displays device pin map with status colors."""

    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.controller = controller
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("Pin Haritası")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.device_label = QLabel("Cihaz seçilmedi")
        layout.addWidget(self.device_label)

        # Legend
        legend_layout = QHBoxLayout()
        for status, color in STATUS_COLORS.items():
            dot = QLabel(f"  {status.value}  ")
            dot.setStyleSheet(
                f"background-color: {color}; color: #1e1e2e; "
                f"border-radius: 3px; padding: 2px 6px; font-size: 11px; font-weight: bold;"
            )
            legend_layout.addWidget(dot)
        legend_layout.addStretch()
        layout.addLayout(legend_layout)

        # Pin table
        self.pin_table = QTableWidget()
        self.pin_table.setColumnCount(7)
        self.pin_table.setHorizontalHeaderLabels([
            "Pin", "Ad", "GPIO", "İşlevler", "Voltaj", "Durum", "Notlar",
        ])
        self.pin_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.pin_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.pin_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.pin_table.verticalHeader().setVisible(False)
        self.pin_table.cellClicked.connect(self._on_pin_clicked)
        layout.addWidget(self.pin_table)

        # Detay paneli
        detail_group = QGroupBox("Pin Detayı")
        detail_layout = QVBoxLayout(detail_group)
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        detail_layout.addWidget(self.detail_text)
        layout.addWidget(detail_group)

        # Güvenlik notu
        warning = QLabel(
            "Yazılımsal pin testleri firmware komut yanıtlarını doğrular. "
            "Fiziksel elektriksel bütünlük için loopback kablolaması gereklidir. "
            "Rezerve/boot pinleri işaretlenmiş ve korumalıdır."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #fab387; font-size: 11px; padding: 8px;")
        layout.addWidget(warning)

    def refresh(self, device_id: str) -> None:
        device = self.controller.get_device(device_id)
        profile = self.controller.get_profile(device_id)

        if not device or not profile:
            self.device_label.setText("Profil mevcut değil")
            self.pin_table.setRowCount(0)
            return

        self.device_label.setText(f"{device.board_model} - {len(profile.pins)} pin tanımlı")
        pins = sorted(profile.pins, key=lambda p: p.number)
        self.pin_table.setRowCount(len(pins))

        for row, pin in enumerate(pins):
            # Determine effective status
            status = pin.status
            if pin.is_reserved:
                status = PinStatus.RESERVED
            elif pin.is_unsafe:
                status = PinStatus.WARNING

            color = STATUS_COLORS.get(status, "#6c7086")

            items = [
                str(pin.number),
                pin.name,
                str(pin.gpio_number) if pin.gpio_number is not None else "-",
                ", ".join(f.value for f in pin.functions),
                f"{pin.voltage_level}V",
                status.value,
                pin.notes,
            ]

            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if col == 5:  # Status column
                    item.setBackground(self._parse_color(color))
                    item.setForeground(self._parse_color("#1e1e2e"))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.pin_table.setItem(row, col, item)

    def _on_pin_clicked(self, row: int, col: int) -> None:
        pin_name = self.pin_table.item(row, 1)
        functions = self.pin_table.item(row, 3)
        notes = self.pin_table.item(row, 6)
        status = self.pin_table.item(row, 5)
        voltage = self.pin_table.item(row, 4)

        if pin_name:
            self.detail_text.setHtml(
                f"<b>Pin:</b> {pin_name.text()}<br>"
                f"<b>İşlevler:</b> {functions.text() if functions else '-'}<br>"
                f"<b>Voltaj:</b> {voltage.text() if voltage else '-'}<br>"
                f"<b>Durum:</b> {status.text() if status else '-'}<br>"
                f"<b>Notlar:</b> {notes.text() if notes else '-'}"
            )

    @staticmethod
    def _parse_color(hex_color: str):
        from PySide6.QtGui import QColor
        return QColor(hex_color)
