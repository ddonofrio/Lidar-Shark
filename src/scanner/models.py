"""Immutable scanner-domain models."""
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class ScannerPoint:
    source_session_id: str
    source_scan_id: int
    sample_index: int
    lidar_angle_deg: float
    range_mm: float
    depth_mm: float
    profile_mm: float
    progression_value: float
    progression_unit: str

@dataclass(frozen=True, slots=True)
class ScannerProfile:
    source_session_id: str
    source_scan_id: int
    timestamp_monotonic_ns: int
    progression_value: float
    points: tuple[ScannerPoint, ...]

@dataclass(slots=True)
class ScannerCapture:
    mode: str
    settings: object
    source_session_id: str | None = None
    started_monotonic_ns: int | None = None
    profiles: list[ScannerProfile] = field(default_factory=list)
    accepted_samples: int = 0
    valid_samples: int = 0
    dropped_scans: int = 0
    degraded_profiles: int = 0

