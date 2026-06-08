from unittest.mock import MagicMock, patch

import pytest

from app.agent.state import AgentState

BASE_STATE: AgentState = {
    "email_id": "msg_001",
    "subject": "My laptop won't boot",
    "body": "I turned it on and nothing happened.",
    "sender": "user@example.com",
    "assigned_team": "",
    "routing_confidence": 0.0,
    "evaluator_verdict": "",
    "supervisor_action": "",
    "final_team": "",
    "ticket_id": "ticket-uuid-1",
}


def _mock_llm_response(content: str):
    mock_response = MagicMock()
    mock_response.content = content
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_response
    return mock_llm


# ── classify_ticket ────────────────────────────────────────────────────────────

def test_classify_ticket_high_confidence():
    mock_llm = _mock_llm_response('{"team": "IT", "confidence": 0.95}')
    with patch("app.agent.nodes._llm", mock_llm):
        from app.agent.nodes import classify_ticket
        result = classify_ticket(BASE_STATE)

    assert result["assigned_team"] == "IT"
    assert result["routing_confidence"] == 0.95


def test_classify_ticket_low_confidence():
    mock_llm = _mock_llm_response('{"team": "Support", "confidence": 0.55}')
    with patch("app.agent.nodes._llm", mock_llm):
        from app.agent.nodes import classify_ticket
        result = classify_ticket(BASE_STATE)

    assert result["assigned_team"] == "Support"
    assert result["routing_confidence"] == 0.55


def test_classify_ticket_unknown_team_zeros_confidence():
    mock_llm = _mock_llm_response('{"team": "Finance", "confidence": 0.9}')
    with patch("app.agent.nodes._llm", mock_llm):
        from app.agent.nodes import classify_ticket
        result = classify_ticket(BASE_STATE)

    assert result["assigned_team"] == "Finance"
    assert result["routing_confidence"] == 0.0


def test_classify_ticket_malformed_json_returns_zero_confidence():
    mock_llm = _mock_llm_response("Sorry, I cannot classify this email.")
    with patch("app.agent.nodes._llm", mock_llm):
        from app.agent.nodes import classify_ticket
        result = classify_ticket(BASE_STATE)

    assert result["assigned_team"] == ""
    assert result["routing_confidence"] == 0.0


def test_classify_ticket_preserves_existing_state_fields():
    mock_llm = _mock_llm_response('{"team": "HR", "confidence": 0.88}')
    with patch("app.agent.nodes._llm", mock_llm):
        from app.agent.nodes import classify_ticket
        result = classify_ticket(BASE_STATE)

    assert result["email_id"] == BASE_STATE["email_id"]
    assert result["ticket_id"] == BASE_STATE["ticket_id"]
    assert result["sender"] == BASE_STATE["sender"]


# ── evaluate_routing ───────────────────────────────────────────────────────────

def test_evaluate_routing_correct():
    state = {**BASE_STATE, "assigned_team": "IT", "routing_confidence": 0.95}
    mock_llm = _mock_llm_response('{"verdict": "correct"}')
    with patch("app.agent.nodes._llm", mock_llm):
        from app.agent.nodes import evaluate_routing
        result = evaluate_routing(state)

    assert result["evaluator_verdict"] == "correct"


def test_evaluate_routing_uncertain():
    state = {**BASE_STATE, "assigned_team": "Support", "routing_confidence": 0.6}
    mock_llm = _mock_llm_response('{"verdict": "uncertain"}')
    with patch("app.agent.nodes._llm", mock_llm):
        from app.agent.nodes import evaluate_routing
        result = evaluate_routing(state)

    assert result["evaluator_verdict"] == "uncertain"


def test_evaluate_routing_incorrect():
    state = {**BASE_STATE, "assigned_team": "HR", "routing_confidence": 0.7}
    mock_llm = _mock_llm_response('{"verdict": "incorrect"}')
    with patch("app.agent.nodes._llm", mock_llm):
        from app.agent.nodes import evaluate_routing
        result = evaluate_routing(state)

    assert result["evaluator_verdict"] == "incorrect"


def test_evaluate_routing_unknown_verdict_defaults_to_uncertain():
    state = {**BASE_STATE, "assigned_team": "IT"}
    mock_llm = _mock_llm_response('{"verdict": "maybe"}')
    with patch("app.agent.nodes._llm", mock_llm):
        from app.agent.nodes import evaluate_routing
        result = evaluate_routing(state)

    assert result["evaluator_verdict"] == "uncertain"


def test_evaluate_routing_malformed_json_defaults_to_uncertain():
    state = {**BASE_STATE, "assigned_team": "IT"}
    mock_llm = _mock_llm_response("I think this looks right.")
    with patch("app.agent.nodes._llm", mock_llm):
        from app.agent.nodes import evaluate_routing
        result = evaluate_routing(state)

    assert result["evaluator_verdict"] == "uncertain"
