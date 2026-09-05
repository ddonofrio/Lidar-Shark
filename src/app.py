import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QGroupBox, QDockWidget, QToolButton
from lidar_sdk.discovery import discover_providers
from .acquisition import AcquisitionController
from .widgets import ScanView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Lidar-Shark"); self.resize(1100,700); self.controller=None
        root=QWidget(); layout=QVBoxLayout(root); self.providers=QComboBox(); self.sources=QComboBox(); self.status=QLabel("Stopped · no acquisition"); self._last_counts=(0, 0)
        toolbar=QGroupBox("Driver and acquisition"); bar=QHBoxLayout(toolbar)
        bar.addWidget(QLabel("Driver")); bar.addWidget(self.providers,1); bar.addWidget(QLabel("Source")); bar.addWidget(self.sources,1)
        self.start_button=QPushButton("▶  Start"); self.stop_button=QPushButton("■  Stop")
        self.start_button.setMinimumWidth(110); self.stop_button.setMinimumWidth(110); self.stop_button.setEnabled(False)
        bar.addWidget(self.start_button); bar.addWidget(self.stop_button)
        self.view=ScanView(); layout.addWidget(toolbar); layout.addWidget(self.view,1); layout.addWidget(self.status); self.setCentralWidget(root)
        self.options_dock=QDockWidget("Display options", self); self.options_dock.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        options=QWidget(); options_layout=QVBoxLayout(options)
        persistence=QGroupBox("Phosphor persistence"); persist_bar=QVBoxLayout(persistence)
        self.persistence_label=QLabel("750 ms"); self.persistence=QSlider(Qt.Horizontal); self.persistence.setRange(50,2000); self.persistence.setValue(750); self.persistence.setToolTip("How long each return remains visible")
        persist_bar.addWidget(self.persistence); persist_bar.addWidget(self.persistence_label)
        color=QGroupBox("Point color"); color_layout=QVBoxLayout(color); self.color_mode=QComboBox(); self.color_mode.addItems(["Uniform", "By range"]); color_layout.addWidget(self.color_mode)
        options_layout.addWidget(persistence); options_layout.addWidget(color); options_layout.addStretch(); self.options_dock.setWidget(options); self.addDockWidget(Qt.RightDockWidgetArea,self.options_dock); self.options_dock.hide()
        self.options_button=QToolButton(); self.options_button.setText("⚙"); self.options_button.setFixedSize(36,32); self.options_button.setToolTip("Display options"); self.options_button.setAccessibleName("Display options")
        bar.addWidget(self.options_button)
        view_menu=self.menuBar().addMenu("View")
        self.options_action=view_menu.addAction("Show display options")
        self.options_action.setCheckable(True); self.options_action.setChecked(False)
        self.loaded, self.diagnostics = discover_providers()
        for p in self.loaded:
            d=p.describe(); self.providers.addItem(f"{d.display_name} ({d.provider_id})",p)
        if not self.loaded:
            self.providers.addItem("No drivers installed", None)
            self.status.setText("No drivers available. Install a lidar-sdk driver and restart.")
        self.providers.currentIndexChanged.connect(self._provider_changed); self.sources.currentIndexChanged.connect(self._apply_source_range); self.start_button.clicked.connect(self.start); self.stop_button.clicked.connect(self.stop); self.options_button.clicked.connect(self._toggle_options); self.options_action.triggered.connect(self._toggle_options); self.options_dock.visibilityChanged.connect(self._options_visibility_changed); self.persistence.valueChanged.connect(self._persistence_changed); self.color_mode.currentTextChanged.connect(self.view.set_color_mode); self._provider_changed(0)
    def _toggle_options(self, checked=False):
        self.options_dock.setVisible(not self.options_dock.isVisible())
    def _options_visibility_changed(self, visible):
        self.options_action.setChecked(visible)
        self.options_button.setText("⚙")
    def _persistence_changed(self,value):
        self.persistence_label.setText(f"{value} ms"); self.view.set_persistence(value)
    def _provider_changed(self,index):
        self.sources.clear()
        provider = self.providers.itemData(index) if index >= 0 else None
        if provider is not None:
            for s in provider.list_sources(): self.sources.addItem(f"{s.display_name} ({s.source_id})",s)
        self._apply_source_range()
    def _apply_source_range(self):
        descriptor=self.sources.currentData()
        configured_range=next((field.default for field in descriptor.fields if field.key == "max_range_mm"), None) if descriptor else None
        self.view.set_sensor_range(configured_range)
    def start(self):
        if self.controller: self.stop()
        if self.providers.currentIndex()<0: self.status.setText("No drivers installed"); return
        provider=self.providers.currentData(); descriptor=self.sources.currentData()
        if provider is None or descriptor is None:
            self.status.setText("No driver/source available. Install a driver and restart.")
            return
        source=provider.create_source(descriptor.source_id,provider.validate_config(descriptor.source_id,{}))
        self._apply_source_range()
        self.controller=AcquisitionController(source); self.controller.scan_received.connect(self._scan_received); self.controller.status.connect(self._source_status); self.controller.failure.connect(self._acquisition_failure); self.controller.start(); self.start_button.setEnabled(False); self.stop_button.setEnabled(True); self.status.setText("Streaming · waiting for data…")
    def _acquisition_failure(self,error):
        self.start_button.setEnabled(True); self.stop_button.setEnabled(False); self.status.setText(f"Acquisition error: {error}")
    def _scan_received(self,scan):
        self.view.set_scan(scan)
        valid=sum(1 for s in scan.sample_status if s.value == 'VALID'); self._last_counts=(valid, scan.sample_count)
        self.status.setText(f"Streaming · scan {scan.scan_id} · {scan.sample_count} samples · valid {valid}")
    def _source_status(self,source_status):
        rate='—' if source_status.scan_rate_hz is None else f"{source_status.scan_rate_hz:.1f} Hz"
        drops=dict(source_status.counters).get('consumer_drops', dict(source_status.counters).get('drops', 0))
        age='—' if source_status.latest_scan_age_s is None else f"{source_status.latest_scan_age_s:.2f} s"
        valid,total=self._last_counts; src=source_status.source
        self.status.setText(f"Streaming · {src.provider_id}/{src.source_kind} · session {src.session_id} · {rate} · latest {age} · {valid}/{total} valid · drops {drops}")
    def stop(self):
        if self.controller:
            controller=self.controller; self.controller=None
            try: controller.stop()
            except Exception as exc: self.status.setText(f"Stop error: {exc}")
        self.start_button.setEnabled(True); self.stop_button.setEnabled(False)
        self.view.clear_scan()
        if not self.status.text().startswith("Stop error"): self.status.setText("Stopped · sensor stopped · canvas cleared")
    def closeEvent(self,event): self.stop(); event.accept()
def main():
    app=QApplication(sys.argv); window=MainWindow(); window.show(); return app.exec()
if __name__=="__main__": main()
