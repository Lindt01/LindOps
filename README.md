# LindOps

![CI](https://github.com/Lindt01/LindOps/actions/workflows/ci.yml/badge.svg)

A self-hosted platform run like a real DevOps/SRE team: Kubernetes, GitOps, monitoring, chaos tests & postmortems.

This repo is built step by step. Right now it runs three self-hosted services with Docker Compose, guarded by a CI pipeline with unit and integration tests.

## Services

| Service | Purpose | URL |
|---|---|---|
| [Gitea](https://about.gitea.com/) | Self-hosted Git server | http://localhost:3000 |
| [Uptime Kuma](https://github.com/louislam/uptime-kuma) | Uptime monitoring | http://localhost:3001 |
| [Vaultwarden](https://github.com/dani-garcia/vaultwarden) | Password manager (Bitwarden-compatible) | http://localhost:8080 |

All images are pinned to fixed versions and every service has a restart policy and a healthcheck.

## Quick start

Requirements: Docker with Docker Compose v2.

```bash
# 1. Create your local config (never committed)
cp compose/.env.example compose/.env
# then set a long random VAULTWARDEN_ADMIN_TOKEN in compose/.env

# 2. Start the stack and wait until every service is healthy
docker compose -f compose/docker-compose.yml up -d --wait

# 3. Check status
docker compose -f compose/docker-compose.yml ps

# Stop (keeps your data)
docker compose -f compose/docker-compose.yml down
```

> On Windows `cmd`, use `copy compose\.env.example compose\.env` for step 1.

## Testing

```bash
pip install -r tests/requirements.txt

# Unit tests: check the compose file against our rules (no containers needed)
pytest tests/unit -v

# Integration tests: run against the started stack
docker compose -f compose/docker-compose.yml up -d --wait
pytest tests/integration -v
```

| Level | What it checks |
|---|---|
| **Validation** | `docker compose config` accepts the compose file |
| **Unit tests** | Every image has a fixed version (no `:latest`), every service has `restart` and a `healthcheck`, no host port is used twice |
| **Integration tests** | All containers are running and `healthy`, every service answers HTTP, Gitea's `/api/healthz` reports `pass` |

## CI pipeline

GitHub Actions runs on every push to `main` and on every pull request:

```
compose-validate ─┐
                  ├──► integration (starts the full stack, runs integration tests, prints logs on failure)
compose-rules ────┘
```

Fast checks run first and in parallel. The slower integration job only starts when both are green.

## Project structure

```
.
├── .github/workflows/ci.yml   # CI pipeline
├── compose/
│   ├── docker-compose.yml     # the stack
│   └── .env.example           # config template (copy to .env)
└── tests/
    ├── requirements.txt       # pinned test dependencies
    ├── unit/                  # rules for the compose file
    └── integration/           # tests against the running stack
```

## Roadmap

- [x] Docker Compose stack (Gitea, Uptime Kuma, Vaultwarden)
- [x] CI: validate the compose file
- [x] Pinned image versions + compose rules as unit tests
- [x] Healthchecks + integration tests in CI
- [ ] Gitea on Postgres + API and database tests
- [ ] End-to-end tests with Playwright
- [ ] Performance tests with k6 (load, stress, spike, soak)
- [ ] Continuous deployment to dedicated homelab hardware
- [ ] Monitoring (Prometheus, Grafana, Loki)
- [ ] Kubernetes (k3s) + GitOps
- [ ] Chaos tests & postmortems

## License

[MIT](LICENSE)