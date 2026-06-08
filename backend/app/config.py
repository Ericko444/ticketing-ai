import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import yaml
from dotenv import load_dotenv

load_dotenv()

VALID_TEAMS = {"IT", "Support", "Helpdesk", "HR"}


@dataclass
class TeamConfig:
    members: List[str]


@dataclass
class Settings:
    anthropic_api_key: str
    gmail_credentials_path: str
    gmail_token_path: str
    gmail_user: str
    gmail_app_password: str
    frontend_url: str
    email_notifications: bool
    supervisor_email: str
    confidence_threshold: float
    polling_interval_seconds: int
    teams: Dict[str, TeamConfig] = field(default_factory=dict)

    def members_for_team(self, team: str) -> List[str]:
        return self.teams.get(team, TeamConfig(members=[])).members


def _load_settings() -> Settings:
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"config.yaml not found at {config_path}")

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    raw_teams = cfg.get("teams", {})
    if not raw_teams:
        raise ValueError("config.yaml must define at least one team")

    for team_name in raw_teams:
        if team_name not in VALID_TEAMS:
            raise ValueError(f"Unknown team '{team_name}' in config.yaml. Valid teams: {VALID_TEAMS}")

    teams = {
        name: TeamConfig(members=data.get("members", []))
        for name, data in raw_teams.items()
    }

    supervisor_email = cfg.get("supervisor", {}).get("email", "")
    if not supervisor_email:
        raise ValueError("config.yaml must define supervisor.email")

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")

    return Settings(
        anthropic_api_key=anthropic_api_key,
        gmail_credentials_path=os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json"),
        gmail_token_path=os.getenv("GMAIL_TOKEN_PATH", "token.json"),
        gmail_user=os.getenv("GMAIL_USER", ""),
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", ""),
        frontend_url=os.getenv("FRONTEND_URL", "http://localhost:3000"),
        email_notifications=os.getenv("EMAIL_NOTIFICATIONS", "true").lower() == "true",
        supervisor_email=supervisor_email,
        confidence_threshold=float(cfg.get("routing", {}).get("confidence_threshold", 0.8)),
        polling_interval_seconds=int(cfg.get("routing", {}).get("polling_interval_seconds", 30)),
        teams=teams,
    )


settings = _load_settings()
