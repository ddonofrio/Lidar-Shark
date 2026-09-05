import pytest

from lidar_sdk.geometry import scan_to_points
from lidar_sdk.models import SampleStatus, Scan2D, SourceInfo

def test_sdk_frame_maps_front_up_and_left_left():
    scan=Scan2D(SourceInfo("fixture","fixture","s"),1,(0.,90.),(1000.,1000.),(SampleStatus.VALID,)*2,1,2)
    points=scan_to_points(scan)
    assert (points[0].x_mm,points[0].y_mm)==(1000.,0.)
    assert points[1].x_mm == pytest.approx(0.0)
    assert points[1].y_mm == pytest.approx(1000.0)
