# Game-Day-Protokoll (während der Übung ausfüllen, nichts nachträglich erfinden)

Datum: ____  Cluster: AKS `aks-pib-dev`  Argo CD Auto-Sync pausiert (root + shop): ja / nein

## Szenario 1: db-down
| Ereignis | Uhrzeit | Notiz |
|---|---|---|
| `./scripts/gameday.sh db-down` ausgeführt | | |
| Erste sichtbare Auswirkung (z. B. `/readyz` 503) | | |
| Alert hat gefeuert (Name) | | |
| Ursache gefunden mit (Befehl, Dashboard, Log) | | |
| Behoben mit | | |
| Normalbetrieb bestätigt | | |

Was lief anders als erwartet?

## Szenario 2: worker-down plus Last
(gleiche Tabelle)

## Szenario 3: bad-deploy
(gleiche Tabelle, ggf. Beobachtung zu Self-Heal)

## Fehler beim Aufbau (alle, auch kleine)
| Schritt | Fehlermeldung | Ursache | Lösung |
|---|---|---|---|
