import json
import subprocess
import urllib.error
import urllib.request
from base64 import b64encode
from pathlib import Path

import yaml

COMPOSE_FILE = Path(__file__).parents[2] / "compose" / "docker-compose.yml"
GITEA_URL = "http://localhost:3000"


def compose(*args, check=True):
    return subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def compose_services():
    with COMPOSE_FILE.open(encoding="utf-8") as f:
        return set(yaml.safe_load(f)["services"])


def running_containers():
    output = compose("ps", "--format", "json").stdout.strip()
    # Depending on the compose version this is a JSON list or one object per line.
    if output.startswith("["):
        containers = json.loads(output)
    else:
        containers = [json.loads(line) for line in output.splitlines() if line]
    return {c["Service"]: c for c in containers}


def http(method, url, auth=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    if auth:
        credentials = b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        request.add_header("Authorization", f"Basic {credentials}")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def psql(query):
    result = compose(
        "exec", "-T", "gitea-db", "psql", "-U", "gitea", "-d", "gitea", "-tAc", query
    )
    return result.stdout.strip()
