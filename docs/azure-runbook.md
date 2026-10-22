# Azure-Durchlauf: Schritt für Schritt (ein Arbeitstag, Kosten bleiben klein)

Ziel: Das Projekt einmal wirklich auf Azure betreiben, Belege sammeln, eine Störung üben und alles wieder löschen.
Dieses Dokument ist eine Checkliste. Die Ergebnisse (Screenshots, Zeiten, Fehler) kommen von dir, nicht aus dem Repo.

## 0. Vorbereitung (30 Minuten)
- [ ] Azure-Konto mit Abo, Spending-Limit oder **Budget-Alarm** einrichten (Portal: Cost Management > Budgets, z. B. 20 EUR, Mail bei 50 % und 80 %).
- [ ] Werkzeuge auf dem Mac: `brew install azure-cli helm kubectl jq` und `brew install hashicorp/tap/terraform`.
- [ ] GitHub-Repository anlegen (öffentlich, damit Argo CD ohne Zugangsdaten lesen kann) und den Code pushen.
- [ ] Lokal prüfen: `make test helm tf-validate`, dann `make up` (oder `make up COMPOSE=docker-compose`) und in einem zweiten Terminal `make smoke`. Fehler zuerst hier beheben (kleine Abweichungen bei Provider-Argumenten oder Chart-Werten sind normal).
- [ ] Notizdatei `docs/game-day-log.md` öffnen. Ab jetzt Uhrzeiten und Fehler mitschreiben (Fehler sind Material für das Post-Mortem).

## 1. Cloud-Zugang und State (README, Abschnitt C, Schritte 1 und 2)
- [ ] `az login`, dann `./scripts/bootstrap-tfstate.sh`
- [ ] `GITHUB_REPO=owner/repo ./scripts/bootstrap-azure-oidc.sh`, die ausgegebenen Werte als GitHub-**Variables** eintragen
- [ ] GitHub Environment `dev` mit Reviewer anlegen
- [ ] Rolle "Storage Blob Data Contributor" für die App auf dem State-Storage vergeben (Befehl steht in der Skriptausgabe)

## 2. Infrastruktur
- [ ] `cd infra/azure/envs/dev && cp terraform.tfvars.example terraform.tfvars` (subscription_id setzen)
- [ ] `terraform init -backend-config=backend.hcl && terraform apply`
- [ ] **Startzeit notieren.** Ab hier laufen Kosten.
- [ ] Output `acr_name` als GitHub-Variable `ACR_NAME` eintragen (vor dem nächsten Push!)
- [ ] Falls der Apply an Kontingent oder Region scheitert: `node_vm_size` oder `location` ändern und das im Log festhalten.

## 3. GitOps
- [ ] `REPO_URL=... SHOP_HOST=... LE_EMAIL=... ./scripts/configure-gitops.sh`, `git diff` ansehen, committen, pushen
- [ ] `./scripts/install-argocd.sh`
- [ ] Warten, bis `kubectl -n argocd get applications` alle Apps zeigt. Pods der Shop-Dienste hängen anfangs in `ImagePullBackOff`, bis der erste CI-Lauf auf `main` die Images gebaut und den Tag eingetragen hat. Das ist erwartet.
- [ ] Optional (nur ein Vorschlag): Ohne eigene Domain kannst du `SHOP_HOST` später auf `shop.<Traefik-IP>.nip.io` setzen. Das Staging-Zertifikat von Let's Encrypt wird vom Browser ohnehin nicht als vertrauenswürdig angezeigt. Für die Demo reicht auch `kubectl port-forward`.

## 4. Belege sammeln (Ordner `docs/screenshots/`)
Immer **Geheimnisse abdecken**: Abo-ID, Tenant-ID, Client-ID, Passwörter, E-Mail-Adressen.

| Datei | Inhalt |
|---|---|
| `01-argocd-apps.png` | Argo CD, alle Apps Synced und Healthy |
| `02-github-actions.png` | Grüner CI-Lauf mit Tests, Trivy, Build, Deploy |
| `03-terraform-plan-pr.png` | Plan-Kommentar auf einem Pull Request |
| `04-azure-resources.png` | Resource Group im Portal |
| `05-grafana-dashboard.png` | Dashboard mit Traffic (vorher ein paar Bestellungen senden) |
| `06-loki-logs.png` | Grafana Explore mit JSON-Logs |
| `07-alert-firing.png` | Alert im Zustand Firing (während des Game Days) |

Zugriff: `kubectl -n argocd port-forward svc/argocd-server 8081:80` und `kubectl -n monitoring port-forward svc/kps-grafana 3000:80`. Grafana-Login: Benutzer `admin`, Passwort aus `kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d` (wird von `install-argocd.sh` erzeugt).

## 5. Game Day (siehe `docs/game-day.md`, jetzt mit fünf Szenarien)
Wichtig: Argo CD macht manuelle Änderungen per Self-Heal rückgängig. Vorher **beide** Apps pausieren, sonst repariert `root` die `shop`-App wieder:
```bash
kubectl -n argocd patch app root --type merge -p '{"spec":{"syncPolicy":{"automated":null}}}'
kubectl -n argocd patch app shop --type merge -p '{"spec":{"syncPolicy":{"automated":null}}}'
```
Danach pro Szenario in `docs/game-day-log.md` festhalten: Uhrzeit Störung, Uhrzeit Alert, Uhrzeit erkannt, Uhrzeit behoben, was du gesehen hast. Danach `./scripts/gameday.sh restore` und die Automatik wieder einschalten:
```bash
kubectl -n argocd patch app root --type merge -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'
kubectl -n argocd patch app shop --type merge -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'
```
Dann das Post-Mortem schreiben (`docs/postmortem-template.md`), und zwar mit **deinen** Zeiten und Beobachtungen.

## 6. Abbauen (nicht vergessen!)
- [ ] Alles Wichtige gesichert: Screenshots, Video, Log, Post-Mortem
- [ ] `cd infra/azure/envs/dev && terraform destroy`
- [ ] State-Storage und App-Registrierung entfernen, wenn du fertig bist (Resource Group aus `bootstrap-tfstate.sh` im Portal löschen)
- [ ] Prüfen: `az group list -o table` zeigt keine `rg-pib-*` mehr
- [ ] Am nächsten Tag in Cost Management nachsehen, dass keine Kosten mehr anfallen
- [ ] Optional AWS: nur ECR und OIDC-Rolle bleiben kostenlos, EKS nur kurz einschalten

## 8. README aktualisieren
- [ ] Abschnitt "Status" ersetzen: Was wurde auf Azure ausgeführt, was nicht, welche Fehler gab es und wie hast du sie behoben
- [ ] Screenshots und Video-Link im Abschnitt "Demo" eintragen
- [ ] Post-Mortem im Repo verlinken
