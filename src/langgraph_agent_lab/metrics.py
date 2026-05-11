"""Utilities for performance measurement and reporting."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from pydantic import BaseModel, Field


class ScenarioMetric(BaseModel):
    """Execution metrics for a single evaluation scenario."""
    scenario_id: str
    success: bool
    expected_route: str
    actual_route: str | None = None
    nodes_visited: int = 0
    retry_count: int = 0
    interrupt_count: int = 0
    approval_required: bool = False
    approval_observed: bool = False
    latency_ms: int = 0
    errors: list[str] = Field(default_factory=list)


class MetricsReport(BaseModel):
    """Aggregate report across all executed scenarios."""
    total_scenarios: int
    success_rate: float
    avg_nodes_visited: float
    total_retries: int
    total_interrupts: int
    resume_success: bool = False
    scenario_metrics: list[ScenarioMetric]


def extract_run_metrics(
    state_snapshot: dict[str, Any], expected_path: str, is_approval_mandatory: bool
) -> ScenarioMetric:
    """Derives performance metrics from the final state of a graph run."""
    history = state_snapshot.get("node_history", []) or []
    logs = state_snapshot.get("execution_log", []) or []
    
    # Fallback for empty history if logs are present
    if not history and logs:
        history = [entry.get("node_name", "unknown") for entry in logs]
        
    stack_trace = state_snapshot.get("error_stack", []) or []
    detected_path = state_snapshot.get("selected_path")
    auth_data = state_snapshot.get("approval_data")
    
    # Calculate retries and interrupts based on node visitation
    retries = sum(1 for tag in history if tag == "increment_retry")
    interrupts = sum(1 for tag in history if tag == "handle_authorization")
    
    is_path_correct = detected_path == expected_path
    has_output = bool(
        state_snapshot.get("final_response") or state_snapshot.get("clarification_needed")
    )
    
    final_success = is_path_correct and has_output
    if is_approval_mandatory:
        final_success = final_success and auth_data is not None
        
    return ScenarioMetric(
        scenario_id=str(state_snapshot.get("scenario_id", "unknown")),
        success=final_success,
        expected_route=expected_path,
        actual_route=detected_path,
        nodes_visited=len(history),
        retry_count=retries,
        interrupt_count=interrupts,
        approval_required=is_approval_mandatory,
        approval_observed=auth_data is not None,
        errors=list(stack_trace),
    )


def generate_aggregate_report(metric_list: list[ScenarioMetric]) -> MetricsReport:
    """Aggregates individual scenario metrics into a single summary report."""
    if not metric_list:
        raise ValueError("Metric list is empty; cannot generate summary.")
        
    return MetricsReport(
        total_scenarios=len(metric_list),
        success_rate=sum(1 for m in metric_list if m.success) / len(metric_list),
        avg_nodes_visited=mean(m.nodes_visited for m in metric_list),
        total_retries=sum(m.retry_count for m in metric_list),
        total_interrupts=sum(m.interrupt_count for m in metric_list),
        resume_success=False,
        scenario_metrics=metric_list,
    )


def save_metrics_to_disk(report_data: MetricsReport, file_path: str | Path) -> None:
    """Serializes the metrics report to a JSON file."""
    target = Path(file_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report_data.model_dump(), indent=2, ensure_ascii=False), 
        encoding="utf-8"
    )
