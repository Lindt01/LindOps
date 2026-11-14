"""Rules for the compose file.

These tests don't start any containers. They only read the YAML file.
"""

from pathlib import Path

import pytest
import yaml

COMPOSE_FILE = Path(__file__).parents[2] / "compose" / "docker-compose.yml"

with COMPOSE_FILE.open(encoding="utf-8") as f:
    SERVICES = yaml.safe_load(f)["services"]


@pytest.mark.parametrize("name", SERVICES.keys())
def test_image_has_fixed_version(name):
    image = SERVICES[name]["image"]
    # The tag is after the last ":" of the last path segment
    # (a ":" before a "/" would be a registry port like localhost:5000/image).
    last_part = image.rsplit("/", 1)[-1]
    assert ":" in last_part, f"{name}: image '{image}' has no tag"
    tag = last_part.split(":", 1)[1]
    assert tag != "latest", f"{name}: image '{image}' uses :latest"


@pytest.mark.parametrize("name", SERVICES.keys())
def test_service_has_restart_policy(name):
    assert "restart" in SERVICES[name], f"{name}: missing 'restart'"


@pytest.mark.parametrize("name", SERVICES.keys())
def test_service_has_healthcheck(name):
    assert "healthcheck" in SERVICES[name], f"{name}: missing 'healthcheck'"


def test_host_ports_are_unique():
    seen = {}
    for name, service in SERVICES.items():
        for port in service.get("ports", []):
            host_port = str(port).split(":")[0]
            assert host_port not in seen, (
                f"port {host_port} is used by '{seen[host_port]}' and '{name}'"
            )
            seen[host_port] = name


@pytest.mark.parametrize(
    "name", [n for n, s in SERVICES.items() if s["image"].startswith("postgres:")]
)
def test_database_is_not_exposed_to_host(name):
    assert "ports" not in SERVICES[name], f"{name}: databases must not publish ports"
