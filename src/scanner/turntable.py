"""Timestamp-based turntable projection."""
from dataclasses import dataclass
import math
from .fov import select_samples
from .models import ScannerPoint, ScannerProfile

@dataclass(frozen=True, slots=True)
class TurntableSettings:
    nominal_rotation_speed_deg_s: float = 6.0
    direction: str = "Clockwise"
    capture_angle_deg: float = 360.0
    fov_deg: float = 180.0
    reverse_profile: bool = False

    @property
    def rpm(self): return self.nominal_rotation_speed_deg_s / 6.0

def project_turntable_profile(scan, session_id: str, t0_ns: int, settings: TurntableSettings) -> ScannerProfile:
    if settings.nominal_rotation_speed_deg_s <= 0 or not 0 < settings.capture_angle_deg <= 360: raise ValueError("invalid turntable settings")
    timestamp = (scan.started_monotonic_ns + scan.ended_monotonic_ns) // 2
    sign = 1.0 if settings.direction == "Clockwise" else -1.0
    rotation = sign * settings.nominal_rotation_speed_deg_s * (timestamp - t0_ns) / 1_000_000_000
    points = []
    for index, angle, distance, signed in select_samples(scan, settings.fov_deg):
        profile = distance * math.sin(math.radians(signed))
        if settings.reverse_profile: profile = -profile
        points.append(ScannerPoint(session_id, scan.scan_id, index, angle, distance, distance * math.cos(math.radians(signed)), profile, rotation, "deg"))
    return ScannerProfile(session_id, scan.scan_id, timestamp, rotation, tuple(points))
