"""Central test engine that orchestrates test execution."""

from __future__ import annotations

import logging
import time
from typing import Callable

from core.connection_manager.connection import ConnectionManager
from core.models import (
    DeviceProfile,
    DiscoveredDevice,
    TestReport,
    TestResult,
    TestResultEntry,
)
from device_plugins.base_plugin import PluginRegistry

logger = logging.getLogger(__name__)


class TestEngine:
    """Orchestrates test execution for any device type."""

    def __init__(
        self,
        plugin_registry: PluginRegistry,
        conn_manager: ConnectionManager,
    ) -> None:
        self.plugins = plugin_registry
        self.conn = conn_manager
        self._stop_requested = False

    def run_quick_test(
        self,
        device: DiscoveredDevice,
        profile: DeviceProfile,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> TestReport:
        """Run quick test suite for a device."""
        plugin = self.plugins.get_plugin_for(device)
        if not plugin:
            return self._no_plugin_report(device)

        test_ids = plugin.get_quick_tests(profile)
        return self._run_tests(device, profile, plugin, test_ids, progress_callback)

    def run_full_test(
        self,
        device: DiscoveredDevice,
        profile: DeviceProfile,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> TestReport:
        """Run full test suite for a device."""
        plugin = self.plugins.get_plugin_for(device)
        if not plugin:
            return self._no_plugin_report(device)

        test_ids = plugin.get_full_tests(profile)
        return self._run_tests(device, profile, plugin, test_ids, progress_callback)

    def run_single_test(
        self,
        device: DiscoveredDevice,
        profile: DeviceProfile,
        test_id: str,
    ) -> TestResultEntry:
        """Run a single specific test."""
        plugin = self.plugins.get_plugin_for(device)
        if not plugin:
            return TestResultEntry(
                test_id=test_id, test_name=test_id,
                result=TestResult.ERROR,
                error_detail="No plugin found for device",
            )
        return plugin.run_test(test_id, device, self.conn, profile)

    def _run_tests(
        self,
        device: DiscoveredDevice,
        profile: DeviceProfile,
        plugin,
        test_ids: list[str],
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> TestReport:
        """Execute a list of tests and build report."""
        self._stop_requested = False
        report = TestReport(
            device_summary=f"{device.board_model} on {device.port or device.ip_address}",
            device_family=device.family.value,
            board_model=device.board_model,
            connection_type=device.connection_type.value,
            confidence=device.confidence,
            total_tests=len(test_ids),
        )

        start_time = time.time()
        for i, test_id in enumerate(test_ids):
            if self._stop_requested:
                remaining = len(test_ids) - i
                report.skipped += remaining
                break

            if progress_callback:
                progress_callback(test_id, i + 1, len(test_ids))

            try:
                result = plugin.run_test(test_id, device, self.conn, profile)
            except Exception as e:
                logger.error("Test %s crashed: %s", test_id, e)
                result = TestResultEntry(
                    test_id=test_id, test_name=test_id,
                    result=TestResult.ERROR,
                    error_detail=str(e),
                    device_type=device.board_model,
                )

            report.results.append(result)
            report.raw_logs.extend(result.log)

            # Count results
            if result.result == TestResult.PASS:
                report.passed += 1
            elif result.result == TestResult.FAIL:
                report.failed += 1
            elif result.result == TestResult.WARNING:
                report.warnings += 1
            elif result.result == TestResult.SKIPPED:
                report.skipped += 1
            elif result.result == TestResult.NOT_SUPPORTED:
                report.unsupported += 1
            elif result.result == TestResult.ERROR:
                report.errors += 1

        report.duration_seconds = time.time() - start_time
        return report

    def _no_plugin_report(self, device: DiscoveredDevice) -> TestReport:
        return TestReport(
            device_summary=f"No plugin for {device.board_model}",
            device_family=device.family.value,
            board_model=device.board_model,
            total_tests=0,
        )

    def stop(self) -> None:
        self._stop_requested = True
