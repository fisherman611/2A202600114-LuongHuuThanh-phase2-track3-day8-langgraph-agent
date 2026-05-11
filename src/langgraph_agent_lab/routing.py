"""Logic for navigating between graph nodes based on current state."""

from __future__ import annotations

from .state import GlobalState, WorkflowPath


def determine_next_step(current_context: GlobalState) -> str:
    """Analyzes the classification outcome to select the appropriate node."""
    target_path = current_context.get("selected_path", WorkflowPath.SIMPLE.value)
    
    # Mapping table for workflow navigation using new node identifiers
    navigation_map = {
        WorkflowPath.SIMPLE.value: "finalize_response",
        WorkflowPath.TOOL.value: "execute_tool_logic",
        WorkflowPath.MISSING_INFO.value: "request_clarification",
        WorkflowPath.RISKY.value: "prepare_sensitive_action",
        WorkflowPath.ERROR.value: "increment_retry",
    }
    
    return navigation_map.get(target_path, "finalize_response")


def eval_retry_status(current_context: GlobalState) -> str:
    """Checks if the maximum number of retries has been reached."""
    current_attempt = int(current_context.get("retry_count", 0))
    threshold = int(current_context.get("limit_retries", 3))
    
    if current_attempt >= threshold:
        return "handle_failure_exhaustion"
    
    return "execute_tool_logic"


def validate_execution_result(current_context: GlobalState) -> str:
    """Determines if the node output is valid or requires a re-run."""
    status = current_context.get("validation_status")
    
    if status == "needs_retry":
        return "increment_retry"
    
    return "finalize_response"


def process_human_feedback(current_context: GlobalState) -> str:
    """Routes the workflow based on the result of a human approval step."""
    feedback = current_context.get("approval_data") or {}
    
    # If explicitly approved, proceed to tool execution; otherwise, request clarification
    if feedback.get("is_approved"):
        return "execute_tool_logic"
    
    return "request_clarification"
