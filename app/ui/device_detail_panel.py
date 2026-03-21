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

        title = QLabel("Cihaz Detayları")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Bilgi grubu
        info_group = QGroupBox("Cihaz Bilgileri")
        info_layout = QVBoxLayout(info_group)

        self.info_labels: dict[str, QLabel] = {}
        for key in ["Model", "Aile", "MCU", "Port/IP", "Bağlantı", "Güven",
                     "VID/PID", "Üretici", "Seri No", "Flash", "RAM", "Özellikler"]:
            row_label = QLabel(f"<b>{key}:</b> --")
            self.info_labels[key] = row_label
            info_layout.addWidget(row_label)

        layout.addWidget(info_group)

        # Yetenekler
        cap_group = QGroupBox("Yetenekler ve Notlar")
        cap_layout = QVBoxLayout(cap_group)
        self.cap_label = QLabel("Detayları görmek için bir cihaz seçin")
        self.cap_label.setWordWrap(True)
        cap_layout.addWidget(self.cap_label)
        layout.addWidget(cap_group)

        # Log
        log_group = QGroupBox("Cihaz Günlüğü")
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
        self.info_labels["Aile"].setText(f"<b>Aile:</b> {device.family.value}")
        self.info_labels["Port/IP"].setText(f"<b>Port/IP:</b> {device.port or device.ip_address}")
        self.info_labels["Bağlantı"].setText(f"<b>Bağlantı:</b> {device.connection_type.value}")
        self.info_labels["Güven"].setText(f"<b>Güven:</b> {device.confidence:.0%}")

        vid = f"0x{device.vid:04X}" if device.vid else "Yok"
        pid = f"0x{device.pid:04X}" if device.pid else "Yok"
        self.info_labels["VID/PID"].setText(f"<b>VID/PID:</b> {vid} / {pid}")
        self.info_labels["Üretici"].setText(f"<b>Üretici:</b> {device.manufacturer or 'Bilinmiyor'}")
        self.info_labels["Seri No"].setText(f"<b>Seri No:</b> {device.serial_number or 'Yok'}")

        if profile:
            self.info_labels["MCU"].setText(f"<b>MCU:</b> {profile.mcu}")
            flash = f"{profile.flash_size_mb} MB" if profile.flash_size_mb else "Yok"
            self.info_labels["Flash"].setText(f"<b>Flash:</b> {flash}")
            ram = f"{profile.ram_kb} KB" if profile.ram_kb else "Yok"
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
            self.info_labels["Özellikler"].setText(f"<b>Özellikler:</b> {', '.join(features) if features else 'Yok'}")

            caps = profile.supported_tests
            notes = profile.notes
            self.cap_label.setText(
                f"<b>Desteklenen testler:</b> {', '.join(caps)}<br><br>"
                f"<b>Notlar:</b> {notes}"
            )
        else:
            self.info_labels["MCU"].setText("<b>MCU:</b> Bilinmiyor")
            self.info_labels["Flash"].setText("<b>Flash:</b> Yok")
            self.info_labels["RAM"].setText("<b>RAM:</b> Yok")
            self.info_labels["Özellikler"].setText("<b>Özellikler:</b> Yok")
            self.cap_label.setText("Bu cihaz için profil yüklenmedi")

    def append_log(self, text: str) -> None:
        self.log_text.appendPlainText(text)
