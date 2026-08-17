# Test Deploy

## GitHub Secrets

The `test-deploy` workflow requires these repository or environment secrets:

- `SSH_HOST` - test server host or IP
- `SSH_PORT` - SSH port, usually `22`
- `SSH_USER` - user used for deployment
- `SSH_PRIVATE_KEY` - private key for `SSH_USER`
- `TEST_DEPLOY_ROOT` - deploy root on the server, for example `/opt/frontend-mdt`
- `TEST_ENV_FILE` - full contents of `.env.test`
- `SSH_KNOWN_HOSTS` - optional known hosts entry for the server

## Server Requirements

The test server must have:

- Docker installed
- `docker compose` available
- the deploy user added to the `docker` group
- write access to `TEST_DEPLOY_ROOT`
- the public key for `SSH_PRIVATE_KEY` added to `~/.ssh/authorized_keys`

The workflow stores releases in:

- `${TEST_DEPLOY_ROOT}/releases/<commit-sha>`
- `${TEST_DEPLOY_ROOT}/current`

Only the last 5 releases are kept.

## How Deployment Works

1. Run the `test-deploy` workflow manually from GitHub Actions.
2. Enter the branch, tag, or commit SHA in `git_ref`.
3. Enter `DEPLOY` in `confirm_deploy`.
4. GitHub uploads the selected repository snapshot to the server.
5. The workflow writes `.env.test`, switches `current`, and runs:

```bash
docker compose --env-file .env.test -f docker-compose.test.yml down --remove-orphans
docker compose --env-file .env.test -f docker-compose.test.yml up --build -d
```

6. The workflow runs smoke checks against `http://127.0.0.1:8000/`, `http://127.0.0.1:8001/`, and `http://127.0.0.1:8002/`.
7. If deploy or smoke checks fail, the workflow switches `current` back to the previous release and starts it again.

## Rollback

Rollback can be done in two ways:

1. Automatic rollback runs if deployment fails after switching to the new release.
2. Manual rollback can be done by re-running the workflow with a previous commit SHA.
