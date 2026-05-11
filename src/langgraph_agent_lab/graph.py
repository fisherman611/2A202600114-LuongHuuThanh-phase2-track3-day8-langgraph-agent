"""Workflow orchestration for the agentic system.

This module constructs the state graph using LangGraph, defining the execution 
flow, conditional branching, and retry mechanisms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph

from .nodes import (
    analyze_intent,
    execute_tool_logic,
    finalize_response,
    handle_authorization,
    handle_failure_exhaustion,
    increment_retry,
    prepare_input,
    prepare_sensitive_action,
    request_clarification,
    verify_result,
    wrap_up_session,
)
from .routing import (
    determine_next_step,
    eval_retry_status,
    process_human_feedback,
    validate_execution_result,
)
from .state import GlobalState


def build_graph(storage: BaseCheckpointSaver | None = None) -> CompiledStateGraph:
    """Configures and compiles the agent's execution graph.

    The workflow follows these high-level stages:
    1. Input Preparation: Sanitizes and initializes the session.
    2. Intent Analysis: Routes the request to the appropriate handler.
    3. Tool Execution: Runs mock utilities with built-in validation loops.
    4. Authorization: Handles sensitive actions through an approval gate.
    5. Finalization: Aggregates results and logs the exit state.
    """
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception as err:
        raise ImportError(
            "LangGraph library is missing. Please ensure it is installed correctly."
        ) from err

    # Initialize graph with the global state schema
    builder = StateGraph(GlobalState)
    
    # Registering processing nodes
    builder.add_node("prepare_input", prepare_input)  # type: ignore[call-overload]
    builder.add_node("analyze_intent", analyze_intent)  # type: ignore[call-overload]
    builder.add_node("finalize_response", finalize_response)  # type: ignore[call-overload]
    builder.add_node("execute_tool_logic", execute_tool_logic)  # type: ignore[call-overload]
    builder.add_node("verify_result", verify_result)  # type: ignore[call-overload]
    builder.add_node("request_clarification", request_clarification)  # type: ignore[call-overload]
    builder.add_node("prepare_sensitive_action", prepare_sensitive_action)  # type: ignore[call-overload]
    builder.add_node("handle_authorization", handle_authorization)  # type: ignore[call-overload]
    builder.add_node("increment_retry", increment_retry)  # type: ignore[call-overload]
    builder.add_node("handle_failure_exhaustion", handle_failure_exhaustion)  # type: ignore[call-overload]
    builder.add_node("wrap_up_session", wrap_up_session)  # type: ignore[call-overload]

    # Defining static and conditional edges
    builder.add_edge(START, "prepare_input")
    builder.add_edge("prepare_input", "analyze_intent")
    
    # Using identity mapping for conditional edges
    builder.add_conditional_edges(
        "analyze_intent", 
        determine_next_step,
        {
            "finalize_response": "finalize_response",
            "execute_tool_logic": "execute_tool_logic",
            "request_clarification": "request_clarification",
            "prepare_sensitive_action": "prepare_sensitive_action",
            "increment_retry": "increment_retry"
        }
    )
    
    builder.add_edge("execute_tool_logic", "verify_result")
    
    builder.add_conditional_edges(
        "verify_result", 
        validate_execution_result,
        {
            "increment_retry": "increment_retry",
            "finalize_response": "finalize_response"
        }
    )
    
    builder.add_edge("request_clarification", "wrap_up_session")
    builder.add_edge("prepare_sensitive_action", "handle_authorization")
    
    builder.add_conditional_edges(
        "handle_authorization", 
        process_human_feedback,
        {
            "execute_tool_logic": "execute_tool_logic",
            "request_clarification": "request_clarification"
        }
    )
    
    builder.add_conditional_edges(
        "increment_retry", 
        eval_retry_status,
        {
            "execute_tool_logic": "execute_tool_logic",
            "handle_failure_exhaustion": "handle_failure_exhaustion"
        }
    )
    
    builder.add_edge("finalize_response", "wrap_up_session")
    builder.add_edge("handle_failure_exhaustion", "wrap_up_session")
    builder.add_edge("wrap_up_session", END)

    return builder.compile(checkpointer=storage)
