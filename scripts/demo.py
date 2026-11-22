import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "REJECTED"}
DEFAULT_CAPTURES_FILE = Path(__file__).resolve().parent / "captures.json"
MIN_CAPTURES = 1
TIMEOUT = 30


class DemoError(Exception):
    pass


class PlannerClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def request(
        self, method: str, path: str, body: dict | None = None
    ) -> tuple[int, dict | None]:
        data = json.dumps(body).encode() if body is not None else None
        request = Request(
            f"{self._base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=TIMEOUT) as response:
                payload = response.read()
                return response.status, json.loads(
                    payload
                ) if payload else None
        except HTTPError as error:
            payload = error.read()
            return error.code, json.loads(payload) if payload else None

    def is_ready(self) -> bool:
        try:
            status, _ = self.request("GET", "/health/ready")
        except (URLError, ConnectionError, TimeoutError):
            return False
        return status == 200

    def create_capture(self, capture: dict) -> None:
        status, body = self.request("POST", "/api/v1/captures", capture)
        if status != 202:
            raise DemoError(
                f"Failed to create {capture['request_id']}: {status} {body}"
            )

    def dispatch_simulation(self) -> tuple[int, dict | None]:
        try:
            return self.request("POST", "/api/v1/simulations")
        except TimeoutError:
            return 0, (
                "Scheduling is still ongoing due to heavy workload. "
                "Retry the entire project with less captures or satellites"
            )

    def get_capture(self, request_id: str) -> dict:
        status, body = self.request("GET", f"/api/v1/captures/{request_id}")
        if status != 200:
            raise DemoError(f"Failed to get {request_id}: {status} {body}")
        return body


class Deadline:
    def __init__(self, seconds: float) -> None:
        self._seconds = seconds
        self._expires_at = time.monotonic() + seconds

    def check(self, reason: str) -> None:
        if time.monotonic() >= self._expires_at:
            raise DemoError(f"Timed out after {self._seconds:.0f}s: {reason}")


def load_captures(path: Path, run_id: str) -> list[dict]:
    try:
        captures = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise DemoError(f"Cannot read captures from {path}: {error}")
    if not isinstance(captures, list) or len(captures) < MIN_CAPTURES:
        raise DemoError(
            f"{path} must contain a list of at least {MIN_CAPTURES} captures"
        )
    return [
        {**capture, "request_id": f"{run_id}-{capture['request_id']}"}
        for capture in captures
    ]


def wait_until_ready(
    client: PlannerClient, deadline: Deadline, poll: float
) -> None:
    print("==> Waiting for planner")
    while not client.is_ready():
        deadline.check("planner not ready")
        time.sleep(poll)


def create_captures(client: PlannerClient, captures: list[dict]) -> None:
    print(f"==> Creating {len(captures)} captures")
    for capture in captures:
        client.create_capture(capture)
        print(
            f"    {capture['request_id']} {capture['target_name']} "
            f"theta={capture['target_theta']:.1f} "
            f"priority={capture['priority']}"
        )


def dispatch_until_drained(
    client: PlannerClient, deadline: Deadline, poll: float
) -> None:
    print("==> Dispatching simulations until the queue is empty")
    while True:
        deadline.check("simulations still pending")
        status, body = client.dispatch_simulation()
        if status == 202:
            print(
                f"    Plan {body['plan_uuid']} dispatched with "
                f"{body['scheduled_captures']} captures"
            )
        elif status == 409:
            time.sleep(poll)
        elif status == 204:
            print("    Nothing left to schedule")
            return
        else:
            raise DemoError(f"Simulation dispatch failed: {status} {body}")


def wait_for_terminal(
    client: PlannerClient,
    request_ids: list[str],
    deadline: Deadline,
    poll: float,
) -> list[dict]:
    print("==> Waiting for captures to reach SUCCEEDED, FAILED or REJECTED")
    while True:
        deadline.check("captures still pending")
        results = [
            client.get_capture(request_id) for request_id in request_ids
        ]
        pending = [r for r in results if r["status"] not in TERMINAL_STATUSES]
        if not pending:
            return results
        print(f"    {len(pending)} captures pending")
        time.sleep(poll)


def print_results(results: list[dict]) -> None:
    headers = ["REQUEST_ID", "STATUS", "SATELLITE", "THETA", "COMPLETED_AT"]
    rows = []
    for result in results:
        details = result.get("execution_details") or {}
        theta = details.get("attempted_at_theta")
        rows.append(
            [
                result["request_id"],
                result["status"],
                result.get("assigned_satellite") or "-",
                f"{theta:.1f}" if theta is not None else "-",
                details.get("completed_at_timestamp") or "-",
            ]
        )
    widths = [max(len(row[i]) for row in [headers, *rows]) for i in range(5)]
    print("==> Results")
    for row in [headers, *rows]:
        print("    " + "  ".join(c.ljust(w) for c, w in zip(row, widths)))
    totals = Counter(result["status"] for result in results)
    print()
    print("    " + "  ".join(f"{s}: {n}" for s, n in sorted(totals.items())))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an end-to-end demo")
    parser.add_argument("--url", default="http://localhost:8080")
    parser.add_argument(
        "--captures-file", type=Path, default=DEFAULT_CAPTURES_FILE
    )
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--poll", type=float, default=2)
    parser.add_argument(
        "--run-id", default=f"demo-{datetime.now():%Y%m%d%H%M%S}"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = PlannerClient(args.url)
    deadline = Deadline(args.timeout)
    try:
        captures = load_captures(args.captures_file, args.run_id)
        wait_until_ready(client, deadline, args.poll)
        create_captures(client, captures)
        dispatch_until_drained(client, deadline, args.poll)
        results = wait_for_terminal(
            client, [c["request_id"] for c in captures], deadline, args.poll
        )
    except DemoError as error:
        print(error, file=sys.stderr)
        return 1
    print_results(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
