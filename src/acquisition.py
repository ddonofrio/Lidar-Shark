from threading import Event, Thread
from PySide6.QtCore import QObject, Signal
from lidar_sdk.errors import DataTimeout

class AcquisitionController(QObject):
    scan_received = Signal(object); source_event = Signal(object); status = Signal(object); failure = Signal(str); finished = Signal()
    def __init__(self, source):
        super().__init__(); self.source=source; self.subscription=None; self._stop=Event(); self._thread=None
    def start(self):
        self._stop.clear(); self.subscription=self.source.subscribe_scans(2); self.source.start()
        self._thread=Thread(target=self._run,name="lidar-shark-acquisition",daemon=True); self._thread.start()
    def _run(self):
        try:
            while not self._stop.is_set():
                try:
                    scan = self.subscription.get(0.25)
                except DataTimeout:
                    # A timeout is a polling interval, not a source failure.
                    continue
                if self._stop.is_set():
                    break
                self.scan_received.emit(scan)
                try:
                    self.status.emit(self.source.get_status())
                except Exception:
                    # A source is allowed not to expose useful live status.
                    pass
        except Exception as exc:
            # Some installed providers expose their equivalent of
            # SubscriptionClosed from their own compatibility layer. Closing
            # a subscription is a normal lifecycle event, never a UI error.
            normal_close = exc.__class__.__name__ in {"SubscriptionClosed", "EndOfStream"}
            if not self._stop.is_set() and not normal_close:
                self.failure.emit(str(exc))
        finally: self.finished.emit()
    def stop(self):
        self._stop.set()
        if self.subscription:
            self.subscription.close()
        try:
            self.source.stop()
        except Exception:
            # Stop is user initiated and must be safe even if the backend
            # already stopped while waking the subscription reader.
            pass
        finally:
            try:
                self.source.close()
            finally:
                if self._thread and self._thread.is_alive():
                    self._thread.join(timeout=1.0)
