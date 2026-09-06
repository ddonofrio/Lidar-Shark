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
    def __post_init__(self):
        if self.nominal_speed_mm_s <= 0 or not math.isfinite(self.nominal_speed_mm_s): raise ValueError("nominal speed must be positive")
        if self.direction not in ("Top to bottom", "Bottom to top"): raise ValueError("invalid linear sweep direction")
        if not 1 <= self.fov_deg <= 360: raise ValueError("field of view must be between 1 and 360 degrees")

def project_linear_profile(scan, session_id: str, t0_ns: int, settings: LinearSweepSettings) -> ScannerProfile:
    timestamp = (scan.started_monotonic_ns + scan.ended_monotonic_ns) // 2
    travel = settings.nominal_speed_mm_s * max(0, timestamp - t0_ns) / 1_000_000_000
    points = []
    for index, angle, distance, signed in select_samples(scan, settings.fov_deg):
        profile = distance * math.sin(math.radians(signed))
        points.append(ScannerPoint(session_id, scan.scan_id, index, angle, distance, distance * math.cos(math.radians(signed)), profile, travel, "mm"))
    return ScannerProfile(session_id, scan.scan_id, timestamp, travel, tuple(points))
