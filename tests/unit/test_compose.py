"""Regeln für die Compose-Datei.

Diese Tests starten keine Container. Sie lesen nur die YAML-Datei
und prüfen, ob unsere eigenen Regeln eingehalten werden.
"""

from pathlib import Path

import pytest
import yaml

COMPOSE_FILE = Path(__file__).parents[2] / "compose" / "docker-compose.yml"


def load_services():
    with COMPOSE_FILE.open(encoding="utf-8") as f:
        compose = yaml.safe_load(f)
    return compose["services"]


SERVICES = load_services()


@pytest.mark.parametrize("name", SERVICES.keys())
def test_image_has_fixed_version(name):
    """Jedes Image braucht eine feste Version, kein :latest und keinen fehlenden Tag."""
    image = SERVICES[name]["image"]
    # Der Tag steht nach dem letzten ":" - aber nur, wenn danach kein "/" mehr kommt
    # (sonst wäre es ein Registry-Port wie localhost:5000/image).
    last_part = image.rsplit("/", 1)[-1]
    assert ":" in last_part, f"{name}: Image '{image}' hat keinen Tag"
    tag = last_part.split(":", 1)[1]
    assert tag != "latest", f"{name}: Image '{image}' nutzt :latest"


@pytest.mark.parametrize("name", SERVICES.keys())
def test_service_has_restart_policy(name):
    """Jeder Dienst muss nach einem Absturz oder Reboot wieder hochkommen."""
    assert "restart" in SERVICES[name], f"{name}: 'restart' fehlt"

@pytest.mark.parametrize("name", SERVICES.keys())
def test_service_has_healthcheck(name):
    """Jeder Dienst braucht einen Healthcheck, damit Docker weiß, ob er wirklich funktioniert."""
    assert "healthcheck" in SERVICES[name], f"{name}: 'healthcheck' fehlt"
    
def test_host_ports_are_unique():
    """Zwei Dienste dürfen nicht denselben Port auf dem Host belegen."""
    seen = {}
    for name, service in SERVICES.items():
        for port in service.get("ports", []):
            host_port = str(port).split(":")[0]
            assert host_port not in seen, (
                f"Port {host_port} wird von '{seen[host_port]}' und '{name}' genutzt"
            )
            seen[host_port] = name