"""Module for generating human-readable evaluation reports."""

from __future__ import annotations

from pathlib import Path

from .metrics import MetricsReport


def generate_markdown_summary(metrics_data: MetricsReport) -> str:
    """Creates a structured Markdown representation of the execution metrics."""
    return f"""# Simulation Performance Analysis
    
## Executive Summary

- **Total Scenarios Evaluated**: {metrics_data.total_scenarios}
- **Success Rate**: {metrics_data.success_rate:.2%}
- **Workflow Efficiency (Avg Nodes)**: {metrics_data.avg_nodes_visited:.2f}
- **Retry Frequency**: {metrics_data.total_retries}
- **Human-in-the-loop Interrupts**: {metrics_data.total_interrupts}

## Implementation Overview

*Provide a detailed analysis of the agent architecture, state management strategies, 
and identified edge cases here.*
"""


def export_report_to_file(metrics_data: MetricsReport, file_path: str | Path) -> None:
    """Saves the generated markdown summary to the specified file system path."""
    target = Path(file_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(generate_markdown_summary(metrics_data), encoding="utf-8")
