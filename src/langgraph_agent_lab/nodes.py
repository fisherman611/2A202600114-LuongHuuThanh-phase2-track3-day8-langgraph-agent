"""Core processing nodes for the agentic workflow.

Each node is designed to be atomic, stateless, and focus on a single 
responsibility within the LangGraph execution cycle.
"""

from __future__ import annotations

import os

from .state import ApprovalDecision, GlobalState, WorkflowPath, record_activity


def prepare_input(current_state: GlobalState) -> dict:
    """Sanitizes and prepares the initial user input for processing."""
    raw_text = current_state.get("user_query", "").strip()
    return {
        "user_query": raw_text,
        "conversation": [f"System: Received input '{raw_text[:30]}...'"],
        "execution_log": [record_activity("prepare_input", "success", "Input normalized")],
        "node_history": ["prepare_input"],
    }


def analyze_intent(current_state: GlobalState) -> dict:
    """Determines the appropriate routing path based on query analysis."""
    text = current_state.get("user_query", "").lower()
    tokens = [t.strip("?!.,;:") for t in text.split()]
    
    # Define triggers for different paths
    triggers = {
        WorkflowPath.RISKY: {"refund", "delete", "send", "cancel", "remove", "revoke"},
        WorkflowPath.TOOL: {"status", "order", "lookup", "check", "track", "find", "search"},
        WorkflowPath.ERROR: {"timeout", "fail", "error", "crash", "unavailable"}
    }
    
    selected_path = WorkflowPath.SIMPLE
    urgency = "low"
    
    # Check for risky operations first
    if any(k in text for k in triggers[WorkflowPath.RISKY]):
        selected_path = WorkflowPath.RISKY
        urgency = "high"
    elif any(k in text for k in triggers[WorkflowPath.TOOL]):
        selected_path = WorkflowPath.TOOL
    elif len(tokens) < 5 and "it" in tokens:
        selected_path = WorkflowPath.MISSING_INFO
    elif any(k in text for k in triggers[WorkflowPath.ERROR]):
        selected_path = WorkflowPath.ERROR

    return {
        "selected_path": selected_path.value,
        "severity": urgency,
        "execution_log": [
            record_activity("analyze_intent", "completed", f"Path set to {selected_path}")
        ],
        "node_history": ["analyze_intent"],
    }


def request_clarification(current_state: GlobalState) -> dict:
    """Constructs a prompt for the user when information is insufficient."""
    msg = "I need more details, such as an order ID, to proceed with your request."
    return {
        "clarification_needed": msg,
        "final_response": msg,
        "execution_log": [
            record_activity("request_clarification", "success", "Feedback requested")
        ],
        "node_history": ["request_clarification"],
    }


def execute_tool_logic(current_state: GlobalState) -> dict:
    """Handles interaction with external mock utilities."""
    current_attempt = int(current_state.get("retry_count", 0))
    scenario = current_state.get("scenario_id", "default")
    
    # Simulate transient errors for specific paths
    if current_state.get("selected_path") == WorkflowPath.ERROR.value and current_attempt < 2:
        output = f"FAULT: intermittent error at attempt {current_attempt} (scenario: {scenario})"
    else:
        output = f"SUCCESS: data retrieved for scenario {scenario}"
        
    return {
        "tool_outputs": [output],
        "execution_log": [
            record_activity("execute_tool", "completed", f"Attempt {current_attempt} finished")
        ],
        "node_history": ["execute_tool"],
    }


def prepare_sensitive_action(current_state: GlobalState) -> dict:
    """Stages an action that requires explicit administrative authorization."""
    return {
        "action_proposal": "Staging restricted operation; awaiting confirmation.",
        "execution_log": [
            record_activity("prepare_sensitive_action", "pending", "Waiting for approval")
        ],
        "node_history": ["prepare_sensitive_action"],
    }


def handle_authorization(current_state: GlobalState) -> dict:
    """Manages the human-in-the-loop approval gate."""
    if os.getenv("LANGGRAPH_INTERRUPT", "").lower() == "true":
        from langgraph.types import interrupt

        raw_response = interrupt({
            "action": current_state.get("action_proposal"),
            "risk": current_state.get("severity"),
        })
        
        if isinstance(raw_response, dict):
            decision = ApprovalDecision(
                is_approved=raw_response.get("is_approved", False),
                justification=raw_response.get("justification", "")
            )
        else:
            decision = ApprovalDecision(is_approved=bool(raw_response))
    else:
        decision = ApprovalDecision(is_approved=True, justification="Automatic bypass enabled")
        
    return {
        "approval_data": decision.model_dump(),
        "execution_log": [
            record_activity(
                "handle_authorization", "completed", f"Approved: {decision.is_approved}"
            )
        ],
        "node_history": ["handle_authorization"],
    }


def increment_retry(current_state: GlobalState) -> dict:
    """Updates the retry counter and records the error state."""
    next_attempt = int(current_state.get("retry_count", 0)) + 1
    return {
        "retry_count": next_attempt,
        "error_stack": [f"Retry triggered. Current count: {next_attempt}"],
        "execution_log": [
            record_activity("increment_retry", "success", f"Iteration {next_attempt}")
        ],
        "node_history": ["increment_retry"],
    }


def finalize_response(current_state: GlobalState) -> dict:
    """Aggregates results into a coherent final response for the user."""
    results = current_state.get("tool_outputs")
    if results:
        response = f"Operation complete. Result: {results[-1]}"
    else:
        response = "The request was processed successfully within the simulation environment."
        
    return {
        "final_response": response,
        "execution_log": [record_activity("finalize_response", "success", "Response generated")],
        "node_history": ["finalize_response"],
    }


def verify_result(current_state: GlobalState) -> dict:
    """Assesses whether the tool output met the required criteria."""
    outputs = current_state.get("tool_outputs", [])
    last_output = outputs[-1] if outputs else ""
    
    if "FAULT" in last_output:
        outcome = "needs_retry"
        detail = "Validation failed: transient fault detected."
    else:
        outcome = "success"
        detail = "Validation passed."
        
    return {
        "validation_status": outcome,
        "execution_log": [record_activity("verify_result", "completed", detail)],
        "node_history": ["verify_result"],
    }


def handle_failure_exhaustion(current_state: GlobalState) -> dict:
    """Provides a terminal response when all retry attempts are exhausted."""
    msg = "Critical failure: the operation could not be completed after maximum retries."
    return {
        "final_response": msg,
        "execution_log": [
            record_activity(
                "failure_exhaustion", 
                "terminal", 
                f"Max retries: {current_state.get('retry_count', 0)}"
            )
        ],
        "node_history": ["failure_exhaustion"],
    }


def wrap_up_session(current_state: GlobalState) -> dict:
    """Performs final auditing and cleanup tasks before exiting."""
    return {
        "validated_route": current_state.get("selected_path", "unknown"),
        "execution_log": [record_activity("wrap_up_session", "finished", "Graph exit reached")],
        "node_history": ["wrap_up_session"],
    }
