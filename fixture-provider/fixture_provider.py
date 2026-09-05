import math, time
from collections import deque
from threading import Condition, Event, Thread
from lidar_sdk.models import *
from lidar_sdk.errors import DataTimeout, SubscriptionClosed

class _Sub:
    def __init__(self,n): self.q=deque(maxlen=n); self.cv=Condition(); self.closed=False; self.drops=0
    def put(self,v):
        with self.cv:
            if self.closed:return
            if len(self.q)==self.q.maxlen:self.q.popleft();self.drops+=1
            self.q.append(v);self.cv.notify()
    def get(self,timeout_s=None):
        with self.cv:
            if not self.q and not self.cv.wait(timeout_s): raise DataTimeout("fixture timeout")
            if self.q:return self.q.popleft()
            raise SubscriptionClosed("fixture subscription closed")
    def close(self):
        with self.cv:self.closed=True;self.cv.notify_all()

class _Source:
    def __init__(self): self.stop_event=Event();self.subs=[];self.thread=None;self.session="fixture-session";self.scan_id=0
    def start(self):
        if self.thread and self.thread.is_alive():return
        self.stop_event.clear();self.thread=Thread(target=self._run,daemon=True);self.thread.start()
    def _run(self):
        while not self.stop_event.wait(.05):
            angles=tuple(float(i*45) for i in range(8)); ranges=(1000.,1000.,0.,1000.,1000.,1000.,1000.,1000.)
            status=tuple(SampleStatus.VALID if r>0 else SampleStatus.NO_RETURN for r in ranges)
            now=time.monotonic_ns(); scan=Scan2D(SourceInfo("fixture","fixture",self.session,"fixture",True,"Deterministic fixture"),self.scan_id,angles,ranges,status,now,now,"simulated",tuple(100. for _ in ranges),True,False)
            self.scan_id+=1
            for sub in tuple(self.subs):sub.put(scan)
    def stop(self): self.stop_event.set(); [s.close() for s in self.subs]
    close=stop
    def subscribe_scans(self,max_queue=2):s=_Sub(max_queue);self.subs.append(s);return s
    def subscribe_events(self,max_queue=32):return _Sub(max_queue)
    def get_latest_scan(self,max_age_s=None):raise Exception("fixture latest scan requires a subscription")
    def get_status(self):return Status(LifecycleState.STREAMING,SourceInfo("fixture","fixture",self.session,"fixture",True),scan_rate_hz=20.)

class FixtureProvider:
    def describe(self):return ProviderDescriptor("fixture","Deterministic fixture","1.0.0",1,"SDK-only test provider")
    def list_sources(self):return (SourceDescriptor("fixture","Deterministic fixture","emulator",frozenset({"intensity"})),)
    def list_devices(self,source_id):return ()
    def validate_config(self,source_id,config):
        if source_id!="fixture" or config:raise ValueError("fixture takes no configuration")
        return ValidatedConfig(())
    def create_source(self,source_id,config):return _Source()
