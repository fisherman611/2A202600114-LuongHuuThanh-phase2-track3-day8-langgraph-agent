from langgraph_agent_lab.scenarios import import_scenario_configs
from langgraph_agent_lab.state import WorkflowPath, Scenario, create_initial_state


def test_scenario_validation():
    scenario = Scenario(id="x", query="hello", expected_route=WorkflowPath.SIMPLE)
    state = create_initial_state(scenario)
    assert state["thread_id"] == "session-x"
    assert state["retry_count"] == 0
    assert state["execution_log"] == []


def test_load_scenarios():
    scenarios = import_scenario_configs("data/sample/scenarios.jsonl")
    assert len(scenarios) >= 6
    assert {item.expected_route for item in scenarios} >= {WorkflowPath.SIMPLE, WorkflowPath.TOOL, WorkflowPath.RISKY}
