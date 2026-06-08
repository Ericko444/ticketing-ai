import os

# Set required env vars before any app module is imported during test collection
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("GMAIL_USER", "test@gmail.com")
os.environ.setdefault("GMAIL_APP_PASSWORD", "test-pass")
