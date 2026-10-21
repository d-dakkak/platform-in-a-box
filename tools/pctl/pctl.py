 #!/usr/bin/env python3
"""pctl: small platform health CLI (stdlib only).

  pctl.py http  URL [URL ...]               HTTP health checks
  pctl.py pods  [-n shop]                   pods that are not healthy (needs kubectl)
  pctl.py queues --url http://localhost:15672 --user guest --password guest
Exit code is 1 when something is unhealthy, so it can be used in scripts and CI.
"""
import argparse
import base64
import json
import subprocess
import sys
import urllib.error
import urllib.request


def check_http(url: str, timeout: float = 3.0) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as res:  # noqa: S310
            return 200 <= res.status < 400, f"HTTP {res.status}"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, f"error: {getattr(exc, 'reason', exc)}"


def unhealthy_pods(pods: dict, max_restarts: int = 5) -> list[str]:
    """Pure function over `kubectl get pods -o json` output."""
    problems = []
    for pod in pods.get("items", []):
        name = pod["metadata"]["name"]
        status = pod.get("status", {})
        phase = status.get("phase", "Unknown")
        if phase == "Succeeded":
            continue
        if phase != "Running":
            problems.append(f"{name}: phase {phase}")
            continue
        for cs in status.get("containerStatuses", []):
            waiting = cs.get("state", {}).get("waiting", {}).get("reason")
            if waiting:
                problems.append(f"{name}/{cs['name']}: {waiting}")
            elif not cs.get("ready"):
                problems.append(f"{name}/{cs['name']}: not ready")
            elif cs.get("restartCount", 0) > max_restarts:
                problems.append(f"{name}/{cs['name']}: {cs['restartCount']} restarts")
    return problems


def queue_depths(queues: list[dict]) -> dict[str, int]:
    """Pure function over the RabbitMQ management API `/api/queues` response."""
    return {q["name"]: q.get("messages_ready", 0) for q in queues}


def cmd_http(args) -> int:
    failed = 0
    for url in args.urls:
        ok, detail = check_http(url, args.timeout)
        print(f"{'OK  ' if ok else 'FAIL'} {url} ({detail})")
        failed += not ok
    return 1 if failed else 0


def cmd_pods(args) -> int:
    out = subprocess.run(
        ["kubectl", "get", "pods", "-n", args.namespace, "-o", "json"],
        check=True, capture_output=True, text=True,
    ).stdout
    problems = unhealthy_pods(json.loads(out), args.max_restarts)
    for p in problems:
        print(f"FAIL {p}")
    if not problems:
        print(f"OK   all pods healthy in namespace {args.namespace}")
    return 1 if problems else 0


def cmd_queues(args) -> int:
    req = urllib.request.Request(f"{args.url.rstrip('/')}/api/queues")
    token = base64.b64encode(f"{args.user}:{args.password}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(req, timeout=5) as res:  # noqa: S310
        depths = queue_depths(json.load(res))
    bad = 0
    for name, ready in sorted(depths.items()):
        flag = "FAIL" if ready > args.max_ready else "OK  "
        bad += ready > args.max_ready
        print(f"{flag} {name}: {ready} ready")
    return 1 if bad else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pctl", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("http", help="HTTP health checks")
    h.add_argument("urls", nargs="+")
    h.add_argument("--timeout", type=float, default=3.0)
    h.set_defaults(func=cmd_http)
    k = sub.add_parser("pods", help="unhealthy pods in a namespace")
    k.add_argument("-n", "--namespace", default="shop")
    k.add_argument("--max-restarts", type=int, default=5)
    k.set_defaults(func=cmd_pods)
    q = sub.add_parser("queues", help="RabbitMQ queue backlog")
    q.add_argument("--url", default="http://localhost:15672")
    q.add_argument("--user", default="guest")
    q.add_argument("--password", default="guest")
    q.add_argument("--max-ready", type=int, default=100)
    q.set_defaults(func=cmd_queues)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
