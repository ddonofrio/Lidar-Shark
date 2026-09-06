"""Bounded capture lifecycle for scanner profiles."""
from .models import ScannerCapture

class ScannerAccumulator:
    def __init__(self, mode, settings, max_profiles=3000, max_points=1_000_000):
        self.capture = ScannerCapture(mode, settings)
        self.max_profiles, self.max_points = max_profiles, max_points
        self.point_count = 0; self.stopped_reason = None; self._scan_ids = set()

    def reset(self):
        self.capture = ScannerCapture(self.capture.mode, self.capture.settings); self.point_count = 0; self.stopped_reason = None; self._scan_ids.clear()

    def add(self, profile):
        if self.stopped_reason: return False
        if self.capture.source_session_id is None: self.capture.source_session_id = profile.source_session_id; self.capture.started_monotonic_ns = profile.timestamp_monotonic_ns
        if profile.source_session_id != self.capture.source_session_id: self.stopped_reason = "Source session changed"; return False
        if profile.source_scan_id in self._scan_ids: self.stopped_reason = "Duplicate scan identity"; return False
        if len(self.capture.profiles) >= self.max_profiles or self.point_count + len(profile.points) > self.max_points: self.stopped_reason = "Capture limit reached"; return False
        self.capture.profiles.append(profile); self._scan_ids.add(profile.source_scan_id); self.point_count += len(profile.points); self.capture.accepted_samples += len(profile.points); return True
