import json
import logging
import re

from app.agent.prompts import CLASSIFY_PROMPT, EVALUATE_PROMPT
from app.agent.state import AgentState
from app.config import settings

logger = logging.getLogger(__name__)

VALID_TEAMS = {"IT", "Support", "Helpdesk", "HR"}


def _build_llm():
    if settings.anthropic_api_key:
        from langchain_anthropic import ChatAnthropic
        logger.info("LLM provider: Anthropic (claude-sonnet-4-6)")
        return ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=settings.anthropic_api_key,
            max_tokens=256,
        )
    from langchain_openai import ChatOpenAI
    logger.info("LLM provider: OpenAI (gpt-4o-mini)")
    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.openai_api_key,
        max_tokens=256,
    )


_llm = _build_llm()


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


def classify_ticket(state: AgentState) -> AgentState:
    # Short-circuit when classification is pre-seeded (e.g. debug/inject with overrides)
    if state.get("assigned_team") and state.get("routing_confidence", 0.0) > 0:
        return state

    prompt = CLASSIFY_PROMPT.format(subject=state["subject"], body=state["body"])
    try:
        response = _llm.invoke(prompt)
        parsed = _parse_json(response.content)
        team = parsed.get("team", "")
        confidence = float(parsed.get("confidence", 0.0))
        if team not in VALID_TEAMS:
            logger.warning("LLM returned unknown team '%s', defaulting confidence to 0.0", team)
            confidence = 0.0
    except Exception:
        logger.exception("classify_ticket failed to parse LLM response")
        team = ""
        confidence = 0.0

    return {**state, "assigned_team": team, "routing_confidence": confidence}


def evaluate_routing(state: AgentState) -> AgentState:
    # Short-circuit when verdict is pre-seeded (e.g. debug/inject with overrides)
    if state.get("evaluator_verdict"):
        return state

    prompt = EVALUATE_PROMPT.format(
        subject=state["subject"],
        body=state["body"],
        assigned_team=state["assigned_team"],
    )
    try:
        response = _llm.invoke(prompt)
        parsed = _parse_json(response.content)
        verdict = parsed.get("verdict", "uncertain")
        if verdict not in {"correct", "uncertain", "incorrect"}:
            verdict = "uncertain"
    except Exception:
        logger.exception("evaluate_routing failed to parse LLM response")
        verdict = "uncertain"

    return {**state, "evaluator_verdict": verdict}
