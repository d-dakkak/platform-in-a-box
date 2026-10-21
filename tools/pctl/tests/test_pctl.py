import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pctl  # noqa: E402


def pod(name, phase="Running", ready=True, restarts=0, waiting=None):
    state = {"waiting": {"reason": waiting}} if waiting else {"running": {}}
    return {
        "metadata": {"name": name},
        "status": {
            "phase": phase,
            "containerStatuses": [
                {"name": "c", "ready": ready, "restartCount": restarts, "state": state}
            ],
        },
    }


class PodTests(unittest.TestCase):
    def test_healthy_pods(self):
        self.assertEqual(pctl.unhealthy_pods({"items": [pod("a"), pod("b")]}), [])

    def test_detects_crashloop_pending_notready_and_restarts(self):
        items = [
            pod("crash", waiting="CrashLoopBackOff"),
            pod("pending", phase="Pending"),
            pod("notready", ready=False),
            pod("flappy", restarts=9),
            pod("done", phase="Succeeded"),
        ]
        problems = pctl.unhealthy_pods({"items": items})
        self.assertEqual(len(problems), 4)
        self.assertTrue(any("CrashLoopBackOff" in p for p in problems))
        self.assertFalse(any("done" in p for p in problems))


class QueueTests(unittest.TestCase):
    def test_queue_depths(self):
        data = [{"name": "q1", "messages_ready": 7}, {"name": "q2"}]
        self.assertEqual(pctl.queue_depths(data), {"q1": 7, "q2": 0})


class ParserTests(unittest.TestCase):
    def test_parser_defaults(self):
        args = pctl.build_parser().parse_args(["pods"])
        self.assertEqual(args.namespace, "shop")


if __name__ == "__main__":
    unittest.main()
