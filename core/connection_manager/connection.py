"""Connection manager for serial and SSH connections."""

from __future__ import annotations

import logging
import time

import paramiko
import serial

from core.models import ConnectionType, DiscoveredDevice, SSHCredentials
from core.protocols.command_protocol import CommandProtocol, SSHCommandAdapter

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages connections to discovered devices."""

    def __init__(self) -> None:
        self._serial_connections: dict[str, serial.Serial] = {}
        self._ssh_connections: dict[str, paramiko.SSHClient] = {}
        self._protocols: dict[str, CommandProtocol] = {}
        self._ssh_adapters: dict[str, SSHCommandAdapter] = {}

    def connect_serial(
        self,
        device: DiscoveredDevice,
        baud_rate: int = 115200,
        timeout: float = 2.0,
    ) -> bool:
        """Open serial connection to device."""
        if device.id in self._serial_connections:
            logger.info("Already connected to %s", device.port)
            return True

        try:
            ser = serial.Serial(
                port=device.port,
                baudrate=baud_rate,
                timeout=timeout,
                write_timeout=timeout,
            )
            time.sleep(0.5)  # Allow device to reset after connection
            self._serial_connections[device.id] = ser
            self._protocols[device.id] = CommandProtocol(ser)
            device.is_connected = True
            logger.info("Connected to %s at %d baud", device.port, baud_rate)
            return True
        except serial.SerialException as e:
            logger.error("Failed to connect to %s: %s", device.port, e)
            return False

    def connect_ssh(
        self,
        device: DiscoveredDevice,
        credentials: SSHCredentials,
    ) -> bool:
        """Open SSH connection to Raspberry Pi Linux device."""
        if device.id in self._ssh_connections:
            logger.info("Already connected to %s", device.ip_address)
            return True

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs: dict = {
                "hostname": credentials.host or device.ip_address,
                "port": credentials.port,
                "username": credentials.username,
                "timeout": 10.0,
            }
            if credentials.key_file:
                connect_kwargs["key_filename"] = credentials.key_file
            elif credentials.password:
                connect_kwargs["password"] = credentials.password

            client.connect(**connect_kwargs)
            self._ssh_connections[device.id] = client
            self._ssh_adapters[device.id] = SSHCommandAdapter(client)
            device.is_connected = True
            logger.info("SSH connected to %s", credentials.host or device.ip_address)
            return True
        except Exception as e:
            logger.error("SSH connection failed: %s", e)
            return False

    def get_protocol(self, device_id: str) -> CommandProtocol | None:
        return self._protocols.get(device_id)

    def get_ssh_adapter(self, device_id: str) -> SSHCommandAdapter | None:
        return self._ssh_adapters.get(device_id)

    def get_serial(self, device_id: str) -> serial.Serial | None:
        return self._serial_connections.get(device_id)

    def disconnect(self, device_id: str) -> None:
        """Disconnect a device."""
        if device_id in self._serial_connections:
            try:
                self._serial_connections[device_id].close()
            except Exception:
                pass
            del self._serial_connections[device_id]
            self._protocols.pop(device_id, None)

        if device_id in self._ssh_connections:
            try:
                self._ssh_connections[device_id].close()
            except Exception:
                pass
            del self._ssh_connections[device_id]
            self._ssh_adapters.pop(device_id, None)

        logger.info("Disconnected device %s", device_id)

    def disconnect_all(self) -> None:
        for device_id in list(self._serial_connections.keys()):
            self.disconnect(device_id)
        for device_id in list(self._ssh_connections.keys()):
            self.disconnect(device_id)

    def is_connected(self, device_id: str) -> bool:
        if device_id in self._serial_connections:
            return self._serial_connections[device_id].is_open
        if device_id in self._ssh_connections:
            transport = self._ssh_connections[device_id].get_transport()
            return transport is not None and transport.is_active()
        return False
