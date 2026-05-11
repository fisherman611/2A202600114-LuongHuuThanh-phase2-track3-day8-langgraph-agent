"""Schema definitions for the LangGraph agent simulation.

This module defines the core data structures used to maintain state across
the graph execution, including routing enums and audit logging schemas.
"""

from __future__ import annotations

from enum import StrEnum
from operator import add
from typing import Annotated, Any, TypedDict

from pydantic import BaseModel, Field, field_validator


class WorkflowPath(StrEnum):
    """Available routing directions for the agent workflow."""
    SIMPLE = "simple"
    TOOL = "tool"
    MISSING_INFO = "missing_info"
    RISKY = "risky"
    ERROR = "error"
    DEAD_LETTER = "dead_letter"
    DONE = "done"


class AuditEntry(BaseModel):
    """A structured log entry for auditing node execution and performance."""

    node_name: str
    status: str
    description: str
    duration_ms: int = 0
    context: dict[str, Any] = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    """Container for human-in-the-loop approval results."""
    is_approved: bool = False
    approver_id: str = "system-default"
    justification: str = ""


class GlobalState(TypedDict, total=False):
    """The central state object for the LangGraph execution environment.
    
    Attributes:
        interaction_id: Unique identifier for the current session.
        scenario_key: ID of the evaluation scenario being executed.
        user_query: The raw input string from the user.
        selected_path: The determined route for the request.
        severity: Risk level assessment of the action.
        retry_count: Current number of attempts for the operation.
        limit_retries: Maximum allowed attempts.
    """

    thread_id: str
    scenario_id: str
    user_query: str
    selected_path: str
    severity: str
    retry_count: int
    limit_retries: int
    final_response: str | None
    clarification_needed: str | None
    action_proposal: str | None
    approval_data: dict[str, Any] | None
    validation_status: str | None
    conversation: Annotated[list[str], add]
    tool_outputs: Annotated[list[str], add]
    error_stack: Annotated[list[str], add]
    execution_log: Annotated[list[dict[str, Any]], add]
    node_history: Annotated[list[str], add]
    validated_route: str


class Scenario(BaseModel):
    """Evaluation scenario configuration."""
    id: str
    query: str
    expected_route: WorkflowPath
    requires_approval: bool = False
    should_retry: bool = False
    max_attempts: int = 3
    tags: list[str] = Field(default_factory=list)

    @field_validator("query")
    @classmethod
    def validate_non_empty_query(cls, text: str) -> str:
        """Ensures the scenario query contains non-whitespace characters."""
        if not text.strip():
            raise ValueError("Scenario query cannot be empty or whitespace only.")
        return text


def create_initial_state(config: Scenario) -> GlobalState:
    """Initializes the state dictionary based on a scenario configuration."""
    return {
        "thread_id": f"session-{config.id}",
        "scenario_id": config.id,
        "user_query": config.query,
        "selected_path": "",
        "severity": "unclassified",
        "retry_count": 0,
        "limit_retries": config.max_attempts,
        "final_response": None,
        "clarification_needed": None,
        "action_proposal": None,
        "approval_data": None,
        "validation_status": None,
        "conversation": [],
        "tool_outputs": [],
        "error_stack": [],
        "execution_log": [],
        "node_history": [],
        "validated_route": "",
    }


def record_activity(
    node: str, status: str, detail: str, **extra_info: object
) -> dict[str, Any]:
    """Helper to generate a dictionary representation of an AuditEntry."""
    return AuditEntry(
        node_name=node, status=status, description=detail, context=extra_info
    ).model_dump()
