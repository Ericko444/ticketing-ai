import json

from app.agent.prompts import CLASSIFY_PROMPT, EVALUATE_PROMPT
from app.agent.state import AgentState


def test_classify_prompt_renders():
    rendered = CLASSIFY_PROMPT.format(
        subject="My laptop won't boot",
        body="I turned it on and nothing happened.",
    )
    assert "IT" in rendered
    assert "My laptop won't boot" in rendered
    assert "confidence" in rendered
    assert "team" in rendered


def test_evaluate_prompt_renders():
    rendered = EVALUATE_PROMPT.format(
        subject="Can't log in",
        body="I forgot my password and the reset email isn't arriving.",
        assigned_team="Helpdesk",
    )
    assert "Helpdesk" in rendered
    assert "verdict" in rendered
    assert "correct" in rendered
    assert "uncertain" in rendered
    assert "incorrect" in rendered


def test_classify_prompt_expects_json_output():
    rendered = CLASSIFY_PROMPT.format(subject="x", body="y")
    # Must mention both fields the LLM must return
    assert '"team"' in rendered
    assert '"confidence"' in rendered


def test_evaluate_prompt_expects_json_output():
    rendered = EVALUATE_PROMPT.format(subject="x", body="y", assigned_team="IT")
    assert '"verdict"' in rendered


def test_agent_state_has_required_keys():
    state: AgentState = {
        "email_id": "msg_001",
        "subject": "test",
        "body": "body",
        "sender": "a@b.com",
        "assigned_team": "IT",
        "routing_confidence": 0.9,
        "evaluator_verdict": "correct",
        "supervisor_action": "",
        "final_team": "IT",
        "ticket_id": "uuid-1",
    }
    assert set(state.keys()) == {
        "email_id", "subject", "body", "sender",
        "assigned_team", "routing_confidence", "evaluator_verdict",
        "supervisor_action", "final_team", "ticket_id",
    }
