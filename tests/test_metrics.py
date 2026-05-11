from langgraph_agent_lab.metrics import extract_run_metrics, generate_aggregate_report
from langgraph_agent_lab.state import record_activity


def test_extract_run_metrics_success():
    state = {
        "scenario_id": "S",
        "selected_path": "simple",
        "final_response": "ok",
        "execution_log": [record_activity("prepare_input", "completed", "ok"), record_activity("finalize_response", "completed", "ok")],
        "error_stack": [],
    }
    metric = extract_run_metrics(state, expected_path="simple", is_approval_mandatory=False)
    assert metric.success is True
    assert metric.nodes_visited == 2


def test_generate_aggregate_report():
    m1 = extract_run_metrics({"scenario_id": "1", "selected_path": "simple", "final_response": "ok", "execution_log": [], "error_stack": []}, "simple", False)
    m2 = extract_run_metrics({"scenario_id": "2", "selected_path": "tool", "final_response": None, "execution_log": [], "error_stack": []}, "tool", False)
    report = generate_aggregate_report([m1, m2])
    assert report.total_scenarios == 2
    assert 0 <= report.success_rate <= 1
