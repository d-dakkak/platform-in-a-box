# Incident management

## Severity
| Level | Meaning | Response |
|---|---|---|
| SEV1 | Ordering unavailable or data at risk | act immediately, one incident lead, updates every 30 min |
| SEV2 | Degraded (slow, delayed events) | handle during working hours, update at start and end |
| SEV3 | No customer impact | ticket, fix in normal flow |

## Roles (small team: one person may hold several)
- **Incident lead:** coordinates, decides, keeps the timeline.
- **Operator:** investigates and applies fixes (follows the runbook).
- **Communicator:** informs stakeholders in plain language (what is affected, what we do, next update time).

## Flow
1. Alert fires (Alertmanager) with a `runbook_url`.
2. Acknowledge, open an incident issue, note the start time.
3. Mitigate first (rollback, scale, restore), investigate root cause afterwards.
4. Confirm recovery with metrics, not feelings.
5. Post-mortem within 3 working days: blameless, focus on system and process (`docs/postmortem-template.md`).
6. Track follow-ups as issues with owners.
