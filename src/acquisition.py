from threading import Event, Thread
from PySide6.QtCore import QObject, Signal
from lidar_sdk.errors import EndOfStream, LidarError

class AcquisitionController(QObject):
    scan_received = Signal(object); source_event = Signal(object); failure = Signal(str); finished = Signal()
    def __init__(self, source):
        super().__init__(); self.source=source; self.subscription=None; self._stop=Event(); self._thread=None
    def start(self):
        self._stop.clear(); self.subscription=self.source.subscribe_scans(2); self.source.start()
        self._thread=Thread(target=self._run,name="lidar-shark-acquisition",daemon=True); self._thread.start()
    def _run(self):
        try:
            while not self._stop.is_set(): self.scan_received.emit(self.subscription.get(0.25))
        except (EndOfStream,LidarError) as exc:
            if not self._stop.is_set(): self.failure.emit(str(exc))
        finally: self.finished.emit()
    def stop(self):
        self._stop.set()
        if self.subscription: self.subscription.close()
        self.source.stop()
