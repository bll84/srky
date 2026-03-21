"""Device detail panel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from app.controllers.app_controller import AppController


class DeviceDetailPanel(QWidget):
    """Shows detailed information about the selected device."""

    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.controller = controller
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("Device Details")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Info group
        info_group = QGroupBox("Device Information")
        info_layout = QVBoxLayout(info_group)

        self.info_labels: dict[str, QLabel] = {}
        for key in ["Model", "Family", "MCU", "Port/IP", "Connection", "Confidence",
                     "VID/PID", "Manufacturer", "Serial", "Flash", "RAM", "Features"]:
            row_label = QLabel(f"<b>{key}:</b> --")
            self.info_labels[key] = row_label
            info_layout.addWidget(row_label)

        layout.addWidget(info_group)

        # Capabilities
        cap_group = QGroupBox("Capabilities & Notes")
        cap_layout = QVBoxLayout(cap_group)
        self.cap_label = QLabel("Select a device to view details")
        self.cap_label.setWordWrap(True)
        cap_layout.addWidget(self.cap_label)
        layout.addWidget(cap_group)

        # Log
        log_group = QGroupBox("Device Log")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)

        layout.addStretch()

    def refresh(self, device_id: str) -> None:
        device = self.controller.get_device(device_id)
        if not device:
            return

        profile = self.controller.get_profile(device_id)

        self.info_labels["Model"].setText(f"<b>Model:</b> {device.board_model}")
        self.info_labels["Family"].setText(f"<b>Family:</b> {device.family.value}")
        self.info_labels["Port/IP"].setText(f"<b>Port/IP:</b> {device.port or device.ip_address}")
        self.info_labels["Connection"].setText(f"<b>Connection:</b> {device.connection_type.value}")
        self.info_labels["Confidence"].setText(f"<b>Confidence:</b> {device.confidence:.0%}")

        vid = f"0x{device.vid:04X}" if device.vid else "N/A"
        pid = f"0x{device.pid:04X}" if device.pid else "N/A"
        self.info_labels["VID/PID"].setText(f"<b>VID/PID:</b> {vid} / {pid}")
        self.info_labels["Manufacturer"].setText(f"<b>Manufacturer:</b> {device.manufacturer or 'N/A'}")
        self.info_labels["Serial"].setText(f"<b>Serial:</b> {device.serial_number or 'N/A'}")

        if profile:
            self.info_labels["MCU"].setText(f"<b>MCU:</b> {profile.mcu}")
            flash = f"{profile.flash_size_mb} MB" if profile.flash_size_mb else "N/A"
            self.info_labels["Flash"].setText(f"<b>Flash:</b> {flash}")
            ram = f"{profile.ram_kb} KB" if profile.ram_kb else "N/A"
            if profile.psram:
                ram += " + PSRAM"
            self.info_labels["RAM"].setText(f"<b>RAM:</b> {ram}")

            features = []
            if profile.wifi:
                features.append("Wi-Fi")
            if profile.bluetooth:
                features.append("Bluetooth")
            if profile.dac_pins:
                features.append("DAC")
            self.info_labels["Features"].setText(f"<b>Features:</b> {', '.join(features) if features else 'N/A'}")

            caps = profile.supported_tests
            notes = profile.notes
            self.cap_label.setText(
                f"<b>Supported tests:</b> {', '.join(caps)}<br><br>"
                f"<b>Notes:</b> {notes}"
            )
        else:
            self.info_labels["MCU"].setText("<b>MCU:</b> Unknown")
            self.info_labels["Flash"].setText("<b>Flash:</b> N/A")
            self.info_labels["RAM"].setText("<b>RAM:</b> N/A")
            self.info_labels["Features"].setText("<b>Features:</b> N/A")
            self.cap_label.setText("No profile loaded for this device")

    def append_log(self, text: str) -> None:
        self.log_text.appendPlainText(text)
