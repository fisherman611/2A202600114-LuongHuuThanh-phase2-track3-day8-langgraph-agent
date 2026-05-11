"""Command-line interface for the agent simulation and evaluation suite."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Annotated

import typer
import yaml

from .graph import build_graph
from .metrics import (
    MetricsReport,
    extract_run_metrics,
    generate_aggregate_report,
    save_metrics_to_disk,
)
from .persistence import initialize_storage_layer
from .report import export_report_to_file
from .scenarios import import_scenario_configs
from .state import create_initial_state

# Disable verbose library warnings for a cleaner CLI output
warnings.filterwarnings(
    "ignore",
    category=PendingDeprecationWarning,
    module="langgraph.checkpoint.serde.encrypted",
)

cli_app = typer.Typer(no_args_is_help=True, help="Agent Simulation CLI Tool")


@cli_app.command("run-scenarios")
def run_scenarios(
    config_file: Annotated[
        Path, typer.Option("--config", help="Path to YAML configuration")
    ],
    results_file: Annotated[
        Path, typer.Option("--output", help="Destination for metrics JSON")
    ],
) -> None:
    """Executes a full evaluation suite based on the provided configuration."""
    # Load configuration
    settings = yaml.safe_load(config_file.read_text(encoding="utf-8"))

    # Initialize components
    scenarios = import_scenario_configs(settings["scenarios_path"])
    storage = initialize_storage_layer(
        settings.get("checkpointer", "memory"), settings.get("database_url")
    )
    workflow = build_graph(storage=storage)

    run_metrics = []
    for scenario in scenarios:
        # Initialize session state
        session_state = create_initial_state(scenario)
        runtime_config = {"configurable": {"thread_id": session_state["thread_id"]}}

        # Execute workflow
        final_output = workflow.invoke(session_state, config=runtime_config)  # type: ignore[call-overload]

        # Collect results
        run_metrics.append(
            extract_run_metrics(
                final_output,
                scenario.expected_route.value,
                scenario.requires_approval,
            )
        )

    # Aggregate and save metrics
    aggregate_report = generate_aggregate_report(run_metrics)
    save_metrics_to_disk(aggregate_report, results_file)

    # Optional report generation
    if settings.get("report_path"):
        export_report_to_file(aggregate_report, settings["report_path"])

    typer.secho(
        f"Evaluation completed. Metrics exported to {results_file}",
        fg=typer.colors.GREEN,
    )


@cli_app.command("validate-metrics")
def validate_metrics(
    metrics_path: Annotated[Path, typer.Option("--metrics", help="Path to metrics JSON")],
) -> None:
    """Verifies the integrity and success rate of a previous evaluation run."""
    raw_data = json.loads(metrics_path.read_text(encoding="utf-8"))
    report = MetricsReport.model_validate(raw_data)

    if report.total_scenarios < 6:
        raise typer.BadParameter(
            "Evaluation must contain at least 6 scenarios to be valid."
        )

    typer.echo(
        f"Metrics verification successful. Current Success Rate: {report.success_rate:.2%}"
    )


if __name__ == "__main__":
    cli_app()
