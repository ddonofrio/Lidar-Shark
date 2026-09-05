import math

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication
from lidar_sdk.models import SampleStatus, Scan2D, SourceInfo

from lidar_shark.widgets import ScanView


def make_scan():
    return Scan2D(
        SourceInfo("fixture", "fixture", "session-1"),
        7,
        (0.0, 90.0, 180.0),
        (1000.0, 2000.0, 3000.0),
        (SampleStatus.VALID, SampleStatus.NO_RETURN, SampleStatus.VALID),
        1,
        2,
    )


def view():
    app = QApplication.instance() or QApplication([])
    result = ScanView()
    result.resize(1000, 1000)
    result.set_sensor_range(5000)
    return app, result


def test_scan_view_keeps_only_valid_returns_and_maps_front_up():
    _, widget = view()
    widget.set_scan(make_scan())

    assert [point.sample_index for point, _ in widget._returns] == [0, 2]
    front = widget._returns[0][0]
    assert widget._point(front) == (500.0, 400.0)


def test_sensor_coordinates_follow_pan_and_recenter():
    _, widget = view()
    center = QPointF(500, 500)
    assert widget._sensor_coordinates(center) == (0.0, 0.0)

    widget.pan_x = 100
    widget.pan_y = -50
    x, y = widget._sensor_coordinates(QPointF(600, 450))
    assert math.isclose(x, 0.0)
    assert math.isclose(y, 0.0)

    widget.recenter()
    assert (widget.pan_x, widget.pan_y) == (0.0, 0.0)


def test_cursor_coordinates_are_normalized_to_zero_to_360_degrees():
    _, widget = view()
    values = []
    widget.mouse_position_changed.connect(values.append)

    widget._emit_mouse_position(QPointF(500, 400))

    assert values[-1] == (0.0, 1000.0)


def test_range_colors_use_documented_distance_bands():
    _, widget = view()
    assert widget._range_color(2000).name() == "#39d353"
    assert widget._range_color(2000.1).name() == "#ffd21f"
    assert widget._range_color(8000.1).name() == "#ff3030"


def test_range_legend_uses_compact_utf8_labels():
    segments = ScanView._range_legend_segments()
    assert [label for _, label, _ in segments] == ["0-2 m", "2-8 m", "8-25 m"]
    assert [precision for _, _, precision in segments] == ["±15 mm", "±20 mm", "±30 mm"]
