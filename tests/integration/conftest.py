import secrets

import pytest

from helpers import compose


@pytest.fixture(scope="session")
def gitea_admin():
    """Admin user for API tests. Returns (username, password)."""
    username = "ci-admin"
    password = secrets.token_urlsafe(16)
    gitea_user = ["exec", "-T", "-u", "git", "gitea", "gitea", "admin", "user"]

    # Fails if the user already exists (e.g. second local run), that's fine.
    compose(
        *gitea_user, "create", "--admin",
        "--username", username,
        "--password", password,
        "--email", f"{username}@example.com",
        "--must-change-password=false",
        check=False,
    )
    # Always set a fresh password so we know it.
    compose(
        *gitea_user, "change-password",
        "--username", username,
        "--password", password,
        "--must-change-password=false",
    )
    return username, password
