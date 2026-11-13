"""Integrationstests: laufen gegen den echten, gestarteten Stack.

Vorher muss der Stack laufen:
    docker compose -f compose/docker-compose.yml up -d --wait
"""

import json
import subprocess
import urllib.request
from pathlib import Path

import pytest
import yaml

COMPOSE_FILE = Path(__file__).parents[2] / "compose" / "docker-compose.yml"

with COMPOSE_FILE.open(encoding="utf-8") as f:
    EXPECTED_SERVICES = set(yaml.safe_load(f)["services"])


def running_containers():
    """Fragt Docker, welche Container zu unserem Stack gehören und wie es ihnen geht."""
    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "ps", "--format", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout.strip()
    # Je nach Compose-Version kommt eine JSON-Liste oder ein JSON-Objekt pro Zeile.
    if output.startswith("["):
        containers = json.loads(output)
    else:
        containers = [json.loads(line) for line in output.splitlines() if line]
    return {c["Service"]: c for c in containers}


def http_get(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status, response.read().decode("utf-8", errors="replace")


def test_all_services_are_up():
    containers = running_containers()
    assert set(containers) == EXPECTED_SERVICES


@pytest.mark.parametrize("name", sorted(EXPECTED_SERVICES))
def test_service_is_running_and_healthy(name):
    container = running_containers()[name]
    assert container["State"] == "running", f"{name}: State ist '{container['State']}'"
    assert container["Health"] == "healthy", f"{name}: Health ist '{container['Health']}'"


@pytest.mark.parametrize(
    "name, url",
    [
        ("gitea", "http://localhost:3000/api/healthz"),
        ("vaultwarden", "http://localhost:8080/alive"),
        ("uptime-kuma", "http://localhost:3001/"),
    ],
)
def test_service_answers_http(name, url):
    status, _ = http_get(url)
    assert status == 200, f"{name}: {url} antwortet mit {status}"


def test_gitea_health_reports_pass():
    _, body = http_get("http://localhost:3000/api/healthz")
    assert json.loads(body)["status"] == "pass"