from langgraph_agent_lab.routing import process_human_feedback, determine_next_step, validate_execution_result, eval_retry_status
from langgraph_agent_lab.state import WorkflowPath


def test_determine_next_step():
    assert determine_next_step({"selected_path": WorkflowPath.SIMPLE.value}) == "finalize_response"
    assert determine_next_step({"selected_path": WorkflowPath.TOOL.value}) == "execute_tool_logic"
    assert determine_next_step({"selected_path": WorkflowPath.RISKY.value}) == "prepare_sensitive_action"


def test_process_human_feedback():
    assert process_human_feedback({"approval_data": {"is_approved": True}}) == "execute_tool_logic"
    assert process_human_feedback({"approval_data": {"is_approved": False}}) == "request_clarification"


def test_eval_retry_status():
    assert eval_retry_status({"retry_count": 0, "limit_retries": 3}) == "execute_tool_logic"
    assert eval_retry_status({"retry_count": 3, "limit_retries": 3}) == "handle_failure_exhaustion"


def test_validate_execution_result():
    assert validate_execution_result({"validation_status": "success"}) == "finalize_response"
    assert validate_execution_result({"validation_status": "needs_retry"}) == "increment_retry"
