import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml
from dotenv import load_dotenv

load_dotenv()

VALID_TEAMS = {"IT", "Support", "Helpdesk", "HR"}


@dataclass
class Settings:
    anthropic_api_key: str
    openai_api_key: str
    gmail_credentials_path: str
    gmail_token_path: str
    gmail_user: str
    gmail_app_password: str
    gmail_enabled: bool
    frontend_url: str
    email_notifications: bool
    email_backend: str  # "log" | "mailtrap" | "gmail"
    mailtrap_user: str
    mailtrap_password: str
    supervisor_email: str
    confidence_threshold: float
    polling_interval_seconds: int
    teams: List[str] = field(default_factory=list)


def _load_settings() -> Settings:
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"config.yaml not found at {config_path}")

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    teams = cfg.get("teams", [])
    if not teams:
        raise ValueError("config.yaml must define at least one team")

    for team_name in teams:
        if team_name not in VALID_TEAMS:
            raise ValueError(f"Unknown team '{team_name}' in config.yaml. Valid teams: {VALID_TEAMS}")

    supervisor_email = cfg.get("supervisor", {}).get("email", "")
    if not supervisor_email:
        raise ValueError("config.yaml must define supervisor.email")

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    if not anthropic_api_key and not openai_api_key:
        raise ValueError(
            "At least one LLM API key is required: set ANTHROPIC_API_KEY or OPENAI_API_KEY"
        )

    return Settings(
        anthropic_api_key=anthropic_api_key,
        openai_api_key=openai_api_key,
        gmail_credentials_path=os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json"),
        gmail_token_path=os.getenv("GMAIL_TOKEN_PATH", "token.json"),
        gmail_user=os.getenv("GMAIL_USER", ""),
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", ""),
        gmail_enabled=os.getenv("GMAIL_ENABLED", "false").lower() == "true",
        frontend_url=os.getenv("FRONTEND_URL", "http://localhost:3000"),
        email_notifications=os.getenv("EMAIL_NOTIFICATIONS", "true").lower() == "true",
        email_backend=os.getenv("EMAIL_BACKEND", "log"),
        mailtrap_user=os.getenv("MAILTRAP_USER", ""),
        mailtrap_password=os.getenv("MAILTRAP_PASSWORD", ""),
        supervisor_email=supervisor_email,
        confidence_threshold=float(cfg.get("routing", {}).get("confidence_threshold", 0.8)),
        polling_interval_seconds=int(cfg.get("routing", {}).get("polling_interval_seconds", 30)),
        teams=teams,
    )


settings = _load_settings()
