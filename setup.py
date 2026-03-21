"""Setup script for DeviceProbe."""

from setuptools import setup, find_packages

setup(
    name="deviceprobe",
    version="1.0.0",
    description="Multi-Device Detection & Test Platform",
    author="DeviceProbe Team",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.5.0",
        "pyserial>=3.5",
        "paramiko>=3.3.0",
    ],
    entry_points={
        "console_scripts": [
            "deviceprobe=main:main",
        ],
    },
)
