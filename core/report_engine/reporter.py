"""Report generation and export."""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime

from core.models import TestReport, TestResult

logger = logging.getLogger(__name__)


class ReportEngine:
    """Generates test reports in multiple formats."""

    @staticmethod
    def to_dict(report: TestReport) -> dict:
        """Convert report to dictionary."""
        return {
            "device_summary": report.device_summary,
            "device_family": report.device_family,
            "board_model": report.board_model,
            "connection_type": report.connection_type,
            "confidence": report.confidence,
            "timestamp": datetime.fromtimestamp(report.timestamp).isoformat(),
            "duration_seconds": round(report.duration_seconds, 2),
            "summary": {
                "total": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "warnings": report.warnings,
                "skipped": report.skipped,
                "unsupported": report.unsupported,
                "errors": report.errors,
            },
            "results": [
                {
                    "test_id": r.test_id,
                    "test_name": r.test_name,
                    "description": r.description,
                    "result": r.result.value,
                    "error_detail": r.error_detail,
                    "recommendation": r.recommendation,
                    "duration": round(r.duration_seconds, 3),
                    "data": r.data,
                    "log": r.log,
                }
                for r in report.results
            ],
        }

    @classmethod
    def to_json(cls, report: TestReport, indent: int = 2) -> str:
        """Export report as JSON string."""
        return json.dumps(cls.to_dict(report), indent=indent, ensure_ascii=False)

    @classmethod
    def to_csv(cls, report: TestReport) -> str:
        """Export report as CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Test ID", "Test Name", "Description", "Result",
            "Error Detail", "Recommendation", "Duration (s)",
        ])
        for r in report.results:
            writer.writerow([
                r.test_id, r.test_name, r.description, r.result.value,
                r.error_detail, r.recommendation, round(r.duration_seconds, 3),
            ])
        return output.getvalue()

    @classmethod
    def to_text(cls, report: TestReport) -> str:
        """Export report as formatted text."""
        lines = [
            "=" * 70,
            "  DeviceProbe Test Report",
            "=" * 70,
            f"  Device: {report.device_summary}",
            f"  Family: {report.device_family}",
            f"  Model:  {report.board_model}",
            f"  Connection: {report.connection_type}",
            f"  Confidence: {report.confidence:.0%}",
            f"  Date: {datetime.fromtimestamp(report.timestamp).strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Duration: {report.duration_seconds:.1f}s",
            "",
            "  Summary:",
            f"    Total:       {report.total_tests}",
            f"    PASS:        {report.passed}",
            f"    FAIL:        {report.failed}",
            f"    WARNING:     {report.warnings}",
            f"    SKIPPED:     {report.skipped}",
            f"    UNSUPPORTED: {report.unsupported}",
            f"    ERROR:       {report.errors}",
            "",
            "-" * 70,
        ]

        for r in report.results:
            icon = {
                TestResult.PASS: "[PASS]",
                TestResult.FAIL: "[FAIL]",
                TestResult.WARNING: "[WARN]",
                TestResult.NOT_SUPPORTED: "[N/S] ",
                TestResult.SKIPPED: "[SKIP]",
                TestResult.ERROR: "[ERR] ",
            }.get(r.result, "[????]")

            lines.append(f"  {icon} {r.test_name}")
            if r.description:
                lines.append(f"         {r.description}")
            if r.error_detail:
                lines.append(f"         Error: {r.error_detail}")
            if r.recommendation:
                lines.append(f"         Rec: {r.recommendation}")
            if r.duration_seconds > 0:
                lines.append(f"         Duration: {r.duration_seconds:.3f}s")
            lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    @classmethod
    def save_json(cls, report: TestReport, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cls.to_json(report))
        logger.info("Report saved to %s", filepath)

    @classmethod
    def save_csv(cls, report: TestReport, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cls.to_csv(report))
        logger.info("CSV report saved to %s", filepath)

    @classmethod
    def save_text(cls, report: TestReport, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cls.to_text(report))
        logger.info("Text report saved to %s", filepath)
