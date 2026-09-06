"""Centred, circular field-of-view selection."""
import math
from lidar_sdk.models import SampleStatus, Scan2D

def signed_angle_deg(angle_deg: float) -> float:
    return ((angle_deg + 180.0) % 360.0) - 180.0

def select_samples(scan: Scan2D, fov_deg: float):
    if not 1 <= fov_deg <= 360:
        raise ValueError("field of view must be between 1 and 360 degrees")
    for index, (angle, distance, status) in enumerate(zip(scan.angles_deg, scan.ranges_mm, scan.sample_status)):
        if status is not SampleStatus.VALID or not math.isfinite(distance) or distance <= 0:
            continue
        signed = signed_angle_deg(angle)
        if fov_deg == 360 or abs(signed) <= fov_deg / 2:
            yield index, angle, float(distance), signed
