"""Device discovery panel - left side of the main window."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from app.controllers.app_controller import AppController


class DeviceDiscoveryPanel(QWidget):
    """Panel for scanning and listing discovered devices."""

    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.controller = controller
        self.setMinimumWidth(320)
        self.setMaximumWidth(450)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("Cihaz Keşfi")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Tarama butonları
        btn_row = QHBoxLayout()
        self.scan_btn = QPushButton("Cihazları Tara")
        self.scan_btn.setObjectName("primaryBtn")
        self.scan_btn.clicked.connect(self._on_scan)
        btn_row.addWidget(self.scan_btn)

        self.refresh_btn = QPushButton("Yenile")
        self.refresh_btn.clicked.connect(self._on_scan)
        btn_row.addWidget(self.refresh_btn)
        layout.addLayout(btn_row)

        # SSH elle giriş
        ssh_group = QGroupBox("SSH Hedefi (Raspberry Pi)")
        ssh_layout = QVBoxLayout(ssh_group)
        self.ssh_host_input = QLineEdit()
        self.ssh_host_input.setPlaceholderText("IP veya hostname (örn: 192.168.1.100)")
        ssh_layout.addWidget(self.ssh_host_input)

        ssh_cred_row = QHBoxLayout()
        self.ssh_user_input = QLineEdit()
        self.ssh_user_input.setPlaceholderText("Kullanıcı (pi)")
        self.ssh_user_input.setText("pi")
        ssh_cred_row.addWidget(self.ssh_user_input)

        self.ssh_pass_input = QLineEdit()
        self.ssh_pass_input.setPlaceholderText("Şifre")
        self.ssh_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        ssh_cred_row.addWidget(self.ssh_pass_input)
        ssh_layout.addLayout(ssh_cred_row)

        self.ssh_add_btn = QPushButton("SSH Hedefi Ekle")
        self.ssh_add_btn.clicked.connect(self._on_add_ssh)
        ssh_layout.addWidget(self.ssh_add_btn)
        layout.addWidget(ssh_group)

        # Cihaz tablosu
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(4)
        self.device_table.setHorizontalHeaderLabels(["Cihaz", "Tür", "Port/IP", "Güven"])
        self.device_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.device_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.device_table.horizontalHeader().resizeSection(3, 50)
        self.device_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.device_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.device_table.verticalHeader().setVisible(False)
        self.device_table.cellClicked.connect(self._on_device_clicked)
        layout.addWidget(self.device_table)

        # Bağlan butonu
        self.connect_btn = QPushButton("Seçilene Bağlan")
        self.connect_btn.setObjectName("primaryBtn")
        self.connect_btn.setEnabled(False)
        self.connect_btn.clicked.connect(self._on_connect)
        layout.addWidget(self.connect_btn)

        self.info_label = QLabel("Başlamak için 'Cihazları Tara' butonuna tıklayın")
        self.info_label.setObjectName("subtitle")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

    def _connect_signals(self) -> None:
        self.controller.devices_updated.connect(self._populate_table)
        self.controller.status_changed.connect(lambda msg: self.info_label.setText(msg))

    def _on_scan(self) -> None:
        self.scan_btn.setEnabled(False)
        self.info_label.setText("Taranıyor...")
        ssh_hosts = []
        if self.ssh_host_input.text().strip():
            ssh_hosts.append(self.ssh_host_input.text().strip())
        self.controller.scan_devices(ssh_hosts=ssh_hosts)
        self.scan_btn.setEnabled(True)

    def _on_add_ssh(self) -> None:
        host = self.ssh_host_input.text().strip()
        if not host:
            self.info_label.setText("Önce bir IP veya hostname girin")
            return
        user = self.ssh_user_input.text().strip() or "pi"
        password = self.ssh_pass_input.text()
        self.controller.add_ssh_device(host, user, password)

    def _populate_table(self) -> None:
        devices = self.controller.get_devices()
        self.device_table.setRowCount(len(devices))
        for row, dev in enumerate(devices):
            self.device_table.setItem(row, 0, QTableWidgetItem(dev.board_model))
            self.device_table.setItem(row, 1, QTableWidgetItem(dev.family.value))
            addr = dev.port or dev.ip_address
            self.device_table.setItem(row, 2, QTableWidgetItem(addr))
            conf_item = QTableWidgetItem(f"{dev.confidence:.0%}")
            conf_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.device_table.setItem(row, 3, conf_item)

        self.info_label.setText(f"{len(devices)} cihaz bulundu")
        self.connect_btn.setEnabled(len(devices) > 0)

    def _on_device_clicked(self, row: int, col: int) -> None:
        devices = self.controller.get_devices()
        if 0 <= row < len(devices):
            self.controller.select_device(devices[row].id)
            self.connect_btn.setEnabled(True)

    def _on_connect(self) -> None:
        self.controller.connect_selected_device()
