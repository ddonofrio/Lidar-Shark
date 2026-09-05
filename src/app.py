import sys
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
from lidar_sdk.discovery import discover_providers
from .acquisition import AcquisitionController
from .widgets import ScanView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Lidar-Shark"); self.resize(1100,700); self.controller=None
        root=QWidget(); layout=QVBoxLayout(root); self.providers=QComboBox(); self.sources=QComboBox(); self.status=QLabel("Stopped")
        self.view=ScanView(); start=QPushButton("Start"); stop=QPushButton("Stop")
        layout.addWidget(self.providers); layout.addWidget(self.sources); layout.addWidget(start); layout.addWidget(stop); layout.addWidget(self.view,1); layout.addWidget(self.status); self.setCentralWidget(root)
        self.loaded, self.diagnostics = discover_providers()
        for p in self.loaded:
            d=p.describe(); self.providers.addItem(f"{d.display_name} ({d.provider_id})",p)
        if not self.loaded:
            self.providers.addItem("No providers installed", None)
            self.status.setText("No providers available. Install a lidar-sdk provider and restart.")
        self.providers.currentIndexChanged.connect(self._provider_changed); start.clicked.connect(self.start); stop.clicked.connect(self.stop); self._provider_changed(0)
    def _provider_changed(self,index):
        self.sources.clear()
        provider = self.providers.itemData(index) if index >= 0 else None
        if provider is not None:
            for s in provider.list_sources(): self.sources.addItem(f"{s.display_name} ({s.source_id})",s)
    def start(self):
        if self.controller: self.stop()
        if self.providers.currentIndex()<0: self.status.setText("No providers installed"); return
        provider=self.providers.currentData(); descriptor=self.sources.currentData()
        if provider is None or descriptor is None:
            self.status.setText("No provider/source available. Install a provider and restart.")
            return
        source=provider.create_source(descriptor.source_id,provider.validate_config(descriptor.source_id,{}))
        self.controller=AcquisitionController(source); self.controller.scan_received.connect(self.view.set_scan); self.controller.failure.connect(lambda e:self.status.setText(f"Error: {e}")); self.controller.start(); self.status.setText("Streaming")
    def stop(self):
        if self.controller: self.controller.stop(); self.controller=None
        self.status.setText("Stopped")
    def closeEvent(self,event): self.stop(); event.accept()
def main():
    app=QApplication(sys.argv); window=MainWindow(); window.show(); return app.exec()
if __name__=="__main__": main()
