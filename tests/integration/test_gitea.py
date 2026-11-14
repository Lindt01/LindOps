"""Gitea API + Postgres tests: create a repo through the API and check
that it really ends up in the database and survives a restart."""

import json
import uuid

import pytest

from helpers import GITEA_URL, compose, http, psql


def repo_count_in_db(owner, name):
    return int(psql(
        "SELECT COUNT(*) FROM repository "
        f"WHERE owner_name = '{owner}' AND lower_name = '{name.lower()}';"
    ))


@pytest.fixture
def repo(gitea_admin):
    owner = gitea_admin[0]
    name = f"test-{uuid.uuid4().hex[:8]}"
    status, body = http(
        "POST", f"{GITEA_URL}/api/v1/user/repos",
        auth=gitea_admin, body={"name": name, "auto_init": True},
    )
    assert status == 201, body
    yield name
    http("DELETE", f"{GITEA_URL}/api/v1/repos/{owner}/{name}", auth=gitea_admin)


def test_gitea_uses_postgres():
    assert psql("SELECT 1;") == "1"
    assert int(psql("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'repository';")) == 1


def test_api_returns_created_repo(gitea_admin, repo):
    status, body = http("GET", f"{GITEA_URL}/api/v1/repos/{gitea_admin[0]}/{repo}", auth=gitea_admin)
    assert status == 200
    assert json.loads(body)["name"] == repo


def test_repo_is_stored_in_postgres(gitea_admin, repo):
    assert repo_count_in_db(gitea_admin[0], repo) == 1


def test_repo_survives_gitea_restart(gitea_admin, repo):
    compose("restart", "gitea")
    compose("up", "-d", "--wait", "gitea")

    status, _ = http("GET", f"{GITEA_URL}/api/v1/repos/{gitea_admin[0]}/{repo}", auth=gitea_admin)
    assert status == 200


def test_deleted_repo_is_removed_from_postgres(gitea_admin, repo):
    owner = gitea_admin[0]
    status, _ = http("DELETE", f"{GITEA_URL}/api/v1/repos/{owner}/{repo}", auth=gitea_admin)
    assert status == 204

    status, _ = http("GET", f"{GITEA_URL}/api/v1/repos/{owner}/{repo}", auth=gitea_admin)
    assert status == 404
    assert repo_count_in_db(owner, repo) == 0
