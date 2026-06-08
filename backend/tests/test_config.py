from app.config import Settings, TeamConfig


def test_members_for_known_team():
    s = Settings(
        anthropic_api_key="k",
        gmail_credentials_path="c.json",
        gmail_token_path="t.json",
        gmail_user="u@g.com",
        gmail_app_password="pass",
        frontend_url="http://localhost:3000",
        email_notifications=True,
        supervisor_email="sup@test.com",
        confidence_threshold=0.8,
        polling_interval_seconds=30,
        teams={"IT": TeamConfig(members=["it@test.com", "it2@test.com"])},
    )
    assert s.members_for_team("IT") == ["it@test.com", "it2@test.com"]


def test_members_for_unknown_team_returns_empty():
    s = Settings(
        anthropic_api_key="k",
        gmail_credentials_path="c.json",
        gmail_token_path="t.json",
        gmail_user="u@g.com",
        gmail_app_password="pass",
        frontend_url="http://localhost:3000",
        email_notifications=True,
        supervisor_email="sup@test.com",
        confidence_threshold=0.8,
        polling_interval_seconds=30,
        teams={},
    )
    assert s.members_for_team("HR") == []


def test_team_config_holds_member_list():
    tc = TeamConfig(members=["a@b.com"])
    assert tc.members == ["a@b.com"]
