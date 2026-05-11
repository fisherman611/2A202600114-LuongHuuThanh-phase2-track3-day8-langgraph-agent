"""Loader for evaluation scenarios."""

from __future__ import annotations

from pathlib import Path

from .state import Scenario


def import_scenario_configs(config_path: str | Path) -> list[Scenario]:
    """Loads and validates a sequence of scenarios from a JSONL file."""
    items: list[Scenario] = []
    
    with Path(config_path).open("r", encoding="utf-8") as stream:
        for idx, line in enumerate(stream, start=1):
            clean_line = line.strip()
            if not clean_line:
                continue
            try:
                items.append(Scenario.model_validate_json(clean_line))
            except Exception as err:
                raise ValueError(f"Failed to parse scenario at line {idx}: {err}") from err
                
    # Validation constraint for grading integrity
    if len(items) < 6:
        raise ValueError(
            f"Insufficient scenarios found ({len(items)}); at least 6 are required for evaluation."
        )
        
    return items
