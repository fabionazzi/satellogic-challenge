import pytest

from src.domain.aggregates.capture import Capture
from src.domain.services.scheduler import ExhaustiveScheduler
from src.domain.value_objects.satellite import Satellite

SATELLITES: dict[str, Satellite] = {
    name: Satellite(
        satellite_id=satellite_id,
        satellite_name=name,
        initial_position=initial_position,
        angular_velocity=1,
        capture_tolerance=2,
        slew_distance=15,
    )
    for satellite_id, (name, initial_position) in enumerate(
        [
            ("sat-alpha", 0),
            ("sat-beta", 90),
            ("sat-gamma", 180),
            ("sat-delta", 270),
        ],
        start=1,
    )
}

CAPTURE_SPECS: dict[str, tuple[float, int]] = {
    "req-01": (10, 1),
    "req-02": (28, 3),
    "req-03": (29, 2),
    "req-04": (12, 0),
    "req-05": (20, 4),
    "req-06": (16, 2),
    "req-07": (190, 0),
    "req-08": (200, 4),
    "req-09": (300, 1),
    "req-10": (359, 3),
}

ALL_SATELLITES = ["sat-alpha", "sat-beta", "sat-gamma", "sat-delta"]


def build_captures(request_ids: list[str]) -> list[Capture]:
    return [
        Capture.create(
            request_id=request_id,
            target_name=f"target-{request_id}",
            target_theta=CAPTURE_SPECS[request_id][0],
            priority=CAPTURE_SPECS[request_id][1],
        )
        for request_id in request_ids
    ]


@pytest.mark.parametrize(
    (
        "satellite_names",
        "request_ids",
        "expected_scheduled",
        "expected_rejected",
    ),
    [
        pytest.param(
            ["sat-alpha"],
            ["req-01", "req-07", "req-09"],
            {"sat-alpha": ["req-01", "req-07", "req-09"]},
            [],
            id="far-apart",
        ),
        pytest.param(
            ["sat-alpha"],
            ["req-01", "req-02"],
            {"sat-alpha": ["req-01"]},
            ["req-02"],
            id="too-close",
        ),
        pytest.param(
            ["sat-alpha"],
            ["req-01", "req-03"],
            {"sat-alpha": ["req-01", "req-03"]},
            [],
            id="exact-min-distance",
        ),
        pytest.param(
            ["sat-alpha"],
            ["req-01", "req-02", "req-03"],
            {"sat-alpha": ["req-01", "req-03"]},
            ["req-02"],
            id="cluster-one-satellite",
        ),
        pytest.param(
            ["sat-alpha", "sat-gamma"],
            ["req-01", "req-02", "req-03"],
            {"sat-alpha": ["req-01", "req-03"], "sat-gamma": ["req-02"]},
            [],
            id="cluster-split-across-satellites",
        ),
        pytest.param(
            ["sat-alpha"],
            ["req-03", "req-06"],
            {"sat-alpha": ["req-06"]},
            ["req-03"],
            id="same-priority-earlier-wins",
        ),
        pytest.param(
            ["sat-gamma"],
            ["req-07", "req-08"],
            {"sat-gamma": ["req-07"]},
            ["req-08"],
            id="lower-priority-value-wins",
        ),
        pytest.param(
            ["sat-alpha"],
            ["req-10"],
            {},
            ["req-10"],
            id="window-crosses-limit",
        ),
        pytest.param(
            ["sat-alpha", "sat-delta"],
            ["req-09", "req-10"],
            {"sat-delta": ["req-09", "req-10"]},
            [],
            id="window-covered-by-other-satellite",
        ),
        pytest.param(
            ["sat-alpha", "sat-beta", "sat-gamma"],
            ["req-01", "req-02", "req-04", "req-05"],
            {
                "sat-alpha": ["req-01"],
                "sat-beta": ["req-02"],
                "sat-gamma": ["req-04"],
            },
            ["req-05"],
            id="three-satellites-dense-cluster",
        ),
        pytest.param(
            ALL_SATELLITES,
            ["req-01", "req-02", "req-04", "req-05", "req-06"],
            {
                "sat-alpha": ["req-01"],
                "sat-beta": ["req-02"],
                "sat-gamma": ["req-06"],
                "sat-delta": ["req-04"],
            },
            ["req-05"],
            id="four-satellites-dense-cluster",
        ),
        pytest.param(
            ALL_SATELLITES,
            ["req-01", "req-02", "req-04", "req-05", "req-06", "req-07"],
            {
                "sat-alpha": ["req-01"],
                "sat-beta": ["req-02"],
                "sat-gamma": ["req-07", "req-06"],
                "sat-delta": ["req-04"],
            },
            ["req-05"],
            id="four-satellites-mixed",
        ),
    ],
)
def test_schedule(
    satellite_names: list[str],
    request_ids: list[str],
    expected_scheduled: dict[str, list[str]],
    expected_rejected: list[str],
) -> None:
    satellites = [SATELLITES[name] for name in satellite_names]
    captures = build_captures(request_ids)

    result = ExhaustiveScheduler().schedule(satellites, captures)

    scheduled = {
        assignment.satellite_name: [
            task.request_id for task in assignment.tasks
        ]
        for assignment in result.scheduled
    }
    assert scheduled == expected_scheduled
    assert result.rejected == expected_rejected
