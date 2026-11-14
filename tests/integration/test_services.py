"""Integration tests against the running stack.

Start it first:
    docker compose -f compose/docker-compose.yml up -d --wait
"""

import json

import pytest

from helpers import GITEA_URL, compose_services, http, running_containers

EXPECTED_SERVICES = compose_services()


def test_all_services_are_up():
    assert set(running_containers()) == EXPECTED_SERVICES


@pytest.mark.parametrize("name", sorted(EXPECTED_SERVICES))
def test_service_is_running_and_healthy(name):
    container = running_containers()[name]
    assert container["State"] == "running", f"{name}: state is '{container['State']}'"
    assert container["Health"] == "healthy", f"{name}: health is '{container['Health']}'"


@pytest.mark.parametrize(
    "name, url",
    [
        ("gitea", f"{GITEA_URL}/api/healthz"),
        ("vaultwarden", "http://localhost:8080/alive"),
        ("uptime-kuma", "http://localhost:3001/"),
    ],
)
def test_service_answers_http(name, url):
    status, _ = http("GET", url)
    assert status == 200, f"{name}: {url} returned {status}"


def test_gitea_health_reports_pass():
    _, body = http("GET", f"{GITEA_URL}/api/healthz")
    health = json.loads(body)
    assert health["status"] == "pass"
    # Only present once Gitea is installed and connected to a database.
    assert health["checks"]["database:ping"][0]["status"] == "pass"
