import importlib.util

import pytest

pytestmark = pytest.mark.skipif(importlib.util.find_spec("langgraph") is None, reason="langgraph not installed in local environment")

from langgraph_agent_lab.graph import build_graph
from langgraph_agent_lab.persistence import initialize_storage_layer
from langgraph_agent_lab.state import WorkflowPath, Scenario, create_initial_state


@pytest.mark.parametrize(
    ("query", "expected_path"),
    [
        ("How do I reset my password?", WorkflowPath.SIMPLE.value),
        ("Please lookup order status for order 123", WorkflowPath.TOOL.value),
        ("Refund this customer", WorkflowPath.RISKY.value),
    ],
)
def test_graph_runs_basic_routes(query, expected_path):
    graph = build_graph(storage=initialize_storage_layer("memory"))
    scenario = Scenario(id="smoke", query=query, expected_route=WorkflowPath(expected_path))
    state = create_initial_state(scenario)
    result = graph.invoke(state, config={"configurable": {"thread_id": state["thread_id"]}})
    assert result["selected_path"] == expected_path
    assert result.get("final_response") or result.get("clarification_needed")
