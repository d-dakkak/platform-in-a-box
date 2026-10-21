# Game day: practising incidents

Goal: prove that alerts fire, runbooks work and you can explain what happened. Run on the dev cluster only.

| # | Scenario | Command | Expected signal | Runbook |
|---|---|---|---|---|
| 1 | Database outage | `./scripts/gameday.sh db-down` then `load 100` | `/readyz` 503, `ShopApiHighErrorRate` | high-error-rate |
| 2 | Consumer down + backlog | `./scripts/gameday.sh worker-down` then `load 300` | `ShopQueueBacklog` after 10 min | queue-backlog |
| 3 | Bad release | `./scripts/gameday.sh bad-deploy` | `ImagePullBackOff`, old pods keep serving | pod-crashloop |
| 4 | Broker outage (relay) | `kubectl -n shop scale statefulset/rabbitmq --replicas=0`, send orders, scale back | orders `pending`, `ShopOrderEventsNotPublished`, then orders reach `created` on their own | queue-backlog |
| 5 | Poison message | publish `not-json` with routing key `order.created` in the RabbitMQ UI (`shop.events`) | `ShopPoisonMessages`, message in the `.dlq` queue | queue-backlog |

Note: Argo CD self-heal may revert scenario 3 on its own. That is a result worth documenting. To observe the failure, pause auto-sync for the `shop` app first.

## Steps
1. Open Grafana ("Shop overview") and the Alertmanager UI.
2. Inject the failure, note the time.
3. Follow only the runbook. Write down every gap.
4. `./scripts/gameday.sh restore`
5. Fill in `docs/postmortem-template.md` (copy it to `docs/postmortems/YYYY-MM-DD-title.md`) and turn gaps into issues.

Keep one finished post-mortem in the repo. It is the best evidence for the "monitoring, logging and incident management" part of the job profile.
