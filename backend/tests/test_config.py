from app.config import Settings


def _settings(**overrides) -> Settings:
    defaults = dict(
        anthropic_api_key="k",
        openai_api_key="",
        gmail_credentials_path="c.json",
        gmail_token_path="t.json",
        gmail_user="u@g.com",
        gmail_app_password="pass",
        gmail_enabled=False,
        frontend_url="http://localhost:3000",
        email_notifications=True,
        email_backend="log",
        mailtrap_user="",
        mailtrap_password="",
        supervisor_email="sup@test.com",
        confidence_threshold=0.8,
        polling_interval_seconds=30,
        teams=[],
    )
    defaults.update(overrides)
    return Settings(**defaults)


def test_teams_is_a_flat_list():
    s = _settings(teams=["IT", "Support", "Helpdesk", "HR"])
    assert s.teams == ["IT", "Support", "Helpdesk", "HR"]


def test_teams_defaults_to_empty_list():
    s = _settings()
    assert s.teams == []
