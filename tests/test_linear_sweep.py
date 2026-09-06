import pytest
from types import SimpleNamespace
from lidar_sdk.models import SampleStatus

from lidar_shark.scanner.linear_sweep import LinearSweepSettings
from lidar_shark.widgets import linear_sweep_x, linear_sweep_y
from lidar_shark.scanner.linear_sweep import project_linear_profile


def test_linear_settings_validate_direction_and_speed():
    assert LinearSweepSettings().direction == "Top to bottom"
    with pytest.raises(ValueError): LinearSweepSettings(0)
    with pytest.raises(ValueError): LinearSweepSettings(1, "sideways")


def test_linear_sweep_coordinates_start_at_edges_and_share_scale():
    assert linear_sweep_y(0, "Top to bottom", 0, 600, 2) == 0
    assert linear_sweep_y(30, "Top to bottom", 0, 600, 2) == 60
    assert linear_sweep_y(0, "Bottom to top", 0, 600, 2) == 600
    assert linear_sweep_y(30, "Bottom to top", 0, 600, 2) == 540
    assert linear_sweep_x(0, 400, 2) == 400
    assert linear_sweep_x(25, 400, 2) == 450
    assert linear_sweep_x(-25, 400, 2) == 350


def test_linear_sweep_uses_midpoint_timestamp_and_non_negative_travel():
    scan = SimpleNamespace(started_monotonic_ns=30_000_000_000, ended_monotonic_ns=30_000_000_000,
                           scan_id=1, angles_deg=(0.0,), ranges_mm=(1000.0,),
                           sample_status=(SampleStatus.VALID,))
    profile = project_linear_profile(scan, "session", 0, LinearSweepSettings(1.0))
    assert profile.progression_value == 30
    assert profile.points[0].profile_mm == 0
    earlier = project_linear_profile(scan, "session", 31_000_000_000, LinearSweepSettings(1.0))
    assert earlier.progression_value == 0
