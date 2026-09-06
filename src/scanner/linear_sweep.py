"""Timestamp-based linear scanner projection."""
from dataclasses import dataclass
import math
from .fov import select_samples
from .models import ScannerPoint, ScannerProfile

@dataclass(frozen=True, slots=True)
class LinearSweepSettings:
    nominal_speed_mm_s: float = 20.0
    direction: str = "Top to bottom"
    fov_deg: float = 180.0
    reverse_profile: bool = False

def project_linear_profile(scan, session_id: str, t0_ns: int, settings: LinearSweepSettings) -> ScannerProfile:
    if settings.nominal_speed_mm_s <= 0: raise ValueError("nominal speed must be positive")
    timestamp = (scan.started_monotonic_ns + scan.ended_monotonic_ns) // 2
    sign = 1.0 if settings.direction == "Top to bottom" else -1.0
    travel = sign * settings.nominal_speed_mm_s * (timestamp - t0_ns) / 1_000_000_000
    points = []
    for index, angle, distance, signed in select_samples(scan, settings.fov_deg):
        profile = distance * math.sin(math.radians(signed))
        if settings.reverse_profile: profile = -profile
        points.append(ScannerPoint(session_id, scan.scan_id, index, angle, distance, distance * math.cos(math.radians(signed)), profile, travel, "mm"))
    return ScannerProfile(session_id, scan.scan_id, timestamp, travel, tuple(points))
