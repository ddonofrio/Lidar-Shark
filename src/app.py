import sys
import math
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPalette
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QFormLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QGroupBox, QDockWidget, QToolButton, QFrame, QStyle
from lidar_sdk.discovery import discover_providers
from .acquisition import AcquisitionController
from .widgets import ScanView
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Lidar-Shark"); self.resize(1100,700); self.controller=None; self.config_widgets={}
        root=QWidget(); layout=QVBoxLayout(root); self.providers=QComboBox(); self.sources=QComboBox(); self.status=QLabel(); self._last_counts=(0, 0); self._mouse_position=None; self._selected_point=None; self._health_text=""; self._stream_text=""
        toolbar=QWidget(); bar=QHBoxLayout(toolbar); bar.setContentsMargins(0,0,0,0)

        self.start_button=QPushButton("▶  Start"); self.stop_button=QPushButton("■  Stop")
        self.start_button.setMinimumWidth(110); self.stop_button.setMinimumWidth(110); self.stop_button.setEnabled(False)
        bar.addWidget(self.start_button); bar.addWidget(self.stop_button)
        self.view=ScanView(); self.config_box=QGroupBox("Source configuration"); self.config_form=QFormLayout(self.config_box); layout.addWidget(self.view,1)
        self.statistics=QLabel("")
        self.statistics.setObjectName("scanStatistics")
        layout.addWidget(self.statistics); self.setCentralWidget(root)
        self.options_dock=QDockWidget("Configuration", self); self.options_dock.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea); self.options_dock.setMinimumWidth(220)
        options=QWidget(); options_layout=QVBoxLayout(options); options_layout.setContentsMargins(6,6,6,6); options_layout.setSpacing(6)
        self.redock_button=QToolButton(); self.redock_button.setIcon(self.style().standardIcon(QStyle.SP_TitleBarNormalButton)); self.redock_button.setToolTip("Dock Configuration"); self.redock_button.setAccessibleName("Dock Configuration"); self.redock_button.setAutoRaise(True); self.redock_button.setFixedSize(24,24); self.redock_button.clicked.connect(self._toggle_dock)
        self.close_config_button=QToolButton(); self.close_config_button.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton)); self.close_config_button.setToolTip("Close Configuration"); self.close_config_button.setAccessibleName("Close Configuration"); self.close_config_button.setAutoRaise(True); self.close_config_button.setFixedSize(24,24); self.close_config_button.clicked.connect(self._close_configuration)
        persistence=QGroupBox("Phosphor persistence"); persist_bar=QVBoxLayout(persistence)
        self.persistence_label=QLabel("750 ms"); self.persistence=QSlider(Qt.Horizontal); self.persistence.setRange(50,2000); self.persistence.setValue(750); self.persistence.setToolTip("How long each return remains visible")
        persist_bar.addWidget(self.persistence); persist_bar.addWidget(self.persistence_label)
        color=QGroupBox("Point color"); color_layout=QVBoxLayout(color); self.color_mode=QComboBox(); self.color_mode.addItems(["Uniform", "By range"]); self.color_mode.setCurrentText("By range"); color_layout.addWidget(self.color_mode)
        driver_box=QGroupBox("Driver and source"); driver_layout=QFormLayout(driver_box)
        driver_layout.addRow("Driver", self.providers); driver_layout.addRow("Source", self.sources); driver_layout.addRow(self.config_box)
        separator=QFrame(); separator.setFrameShape(QFrame.HLine); separator.setFrameShadow(QFrame.Sunken)
        display_box=QGroupBox("Display options"); display_layout=QVBoxLayout(display_box)
        display_layout.addWidget(persistence); display_layout.addWidget(color)
        self.show_color_range=QCheckBox("Show color range"); self.show_color_range.setChecked(True)
        self.show_grid=QCheckBox("Show grid"); self.show_grid.setChecked(True)
        display_layout.addWidget(self.show_color_range); display_layout.addWidget(self.show_grid)
        options_layout.addWidget(driver_box); options_layout.addWidget(separator); options_layout.addWidget(display_box); options_layout.addStretch()
        self.options_dock.setWidget(options); self.addDockWidget(Qt.RightDockWidgetArea,self.options_dock); self.options_dock.hide()
        titlebar=QWidget(); titlebar_layout=QHBoxLayout(titlebar); titlebar_layout.setContentsMargins(8,0,2,0); titlebar_layout.setSpacing(2); titlebar_layout.addWidget(QLabel("Configuration")); titlebar_layout.addStretch(); titlebar_layout.addWidget(self.redock_button); titlebar_layout.addWidget(self.close_config_button); self.options_dock.setTitleBarWidget(titlebar)
        self.options_dock.topLevelChanged.connect(self._configuration_floating_changed)
        for label in toolbar.findChildren(QLabel): label.hide()
        self.start_button.setText(""); self.stop_button.setText("")
        self.start_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay)); self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.start_button.setToolTip("Start"); self.stop_button.setToolTip("Stop"); self.start_button.setAccessibleName("Start"); self.stop_button.setAccessibleName("Stop")
        self.start_button.setFixedSize(36,32); self.stop_button.setFixedSize(36,32)
        self.start_button.setObjectName("startButton"); self.stop_button.setObjectName("stopButton")
        for button in (self.start_button, self.stop_button):
            palette=button.palette()
            palette.setColor(QPalette.Button, palette.color(QPalette.Highlight))
            palette.setColor(QPalette.ButtonText, palette.color(QPalette.HighlightedText))
            button.setPalette(palette)
        root.setStyleSheet("""
            QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #8aa095; border-radius: 3px; background: #18241f; }
            QCheckBox::indicator:checked { background: #2fbf71; border-color: #8ff0b7; }
            QCheckBox::indicator:unchecked { background: #26302c; }
        """)
        self.options_button=QToolButton(); self.options_button.setText("⚙"); self.options_button.setFixedSize(36,32); self.options_button.setToolTip("Display options"); self.options_button.setAccessibleName("Display options")
        bar.removeWidget(self.options_button); self.options_button.setParent(None); self.options_button.setText("\u2699"); self.options_button.setToolTip("Open Configuration"); self.options_button.setAccessibleName("Open Configuration"); self.options_button.setAutoRaise(True); self.options_button.setFixedSize(36,32)
        header=QWidget(); header_layout=QHBoxLayout(header); header_layout.setContentsMargins(0,0,0,0); header_layout.addWidget(toolbar); header_layout.addStretch(); header_layout.addWidget(self.options_button); layout.insertWidget(0,header)
        self._configuration_floating_changed(self.options_dock.isFloating())
        self.loaded, self.diagnostics = discover_providers()
        for p in self.loaded:
            d=p.describe(); self.providers.addItem(f"{d.display_name} ({d.provider_id})",p)
        if not self.loaded:
            self.providers.addItem("No drivers installed", None)
            self._set_health("No drivers available. Install a lidar-sdk driver and restart.")
        self.providers.currentIndexChanged.connect(self._provider_changed); self.sources.currentIndexChanged.connect(self._apply_source_range); self.start_button.clicked.connect(self.start); self.stop_button.clicked.connect(self.stop); self.options_button.clicked.connect(self._toggle_options); self.options_dock.visibilityChanged.connect(self._options_visibility_changed); self.persistence.valueChanged.connect(self._persistence_changed); self.color_mode.currentTextChanged.connect(self.view.set_color_mode); self.show_color_range.toggled.connect(self.view.set_show_color_range); self.show_grid.toggled.connect(self.view.set_show_grid); self.view.mouse_position_changed.connect(self._mouse_position_changed); self.view.sample_selected.connect(self._sample_selected); self.view.set_color_mode("By range"); self.view.set_show_color_range(True); self.view.set_show_grid(True); self._provider_changed(0)
    def _toggle_options(self, checked=False):
        if self.options_dock.isVisible():
            self.options_dock.hide()
        else:
            self.options_dock.setFloating(False)
            self.options_dock.show()
    def _toggle_dock(self):
        self.options_dock.setFloating(not self.options_dock.isFloating())
        self.options_dock.show()
    def _close_configuration(self):
        self.options_dock.hide()
    def _options_visibility_changed(self, visible):
        self.options_button.setText("⚙")
    def _configuration_floating_changed(self, floating):
        self.redock_button.setVisible(True)
        action="Dock" if floating else "Undock"
        icon=QStyle.SP_ArrowLeft if floating else QStyle.SP_ArrowRight
        self.redock_button.setIcon(self.style().standardIcon(icon))
        self.redock_button.setToolTip(f"{action} Configuration")
        self.redock_button.setAccessibleName(f"{action} Configuration")
        if floating:
            self.options_dock.widget().adjustSize()
            self.options_dock.adjustSize()
            self.options_dock.resize(self.options_dock.sizeHint())
    def _persistence_changed(self,value):
        self.persistence_label.setText(f"{value} ms"); self.view.set_persistence(value)
    def _mouse_position_changed(self,position):
        self._mouse_position=position
        mouse = "" if position is None else f"{position[0]:.2f}° · {position[1]:.0f} mm ({position[1] / 1000:.2f} m)"
        valid, total = self._last_counts
        scan = "" if self.view.scan is None else f"Scan: {self.view.scan.scan_id} · {valid}/{total} valid"
        selection = "" if self._selected_point is None else f"Selection: sample {self._selected_point.sample_index} · {math.hypot(self._selected_point.x_mm, self._selected_point.y_mm):.0f} mm"
        self.statistics.setText(" | ".join(value for value in (mouse, scan, self._stream_text, self._health_text, selection) if value))
    def _set_health(self,text):
        self._health_text=text
        self._mouse_position_changed(self._mouse_position)
    def _sample_selected(self, point):
        self._selected_point=point
        self._mouse_position_changed(self._mouse_position)
        self._set_health(f"Selected point · sample {point.sample_index} · X {point.x_mm:.0f} mm · Y {point.y_mm:.0f} mm")
    def _provider_changed(self,index):
        self.sources.clear()
        self._clear_config()
        provider = self.providers.itemData(index) if index >= 0 else None
        if provider is not None:
            for s in provider.list_sources(): self.sources.addItem(f"{s.display_name} ({s.source_id})",s)
        self._apply_source_range()
        self._build_config(self.sources.currentData())
    def _apply_source_range(self):
        descriptor=self.sources.currentData()
        configured_range=next((field.default for field in descriptor.fields if field.key == "max_range_mm"), None) if descriptor else None
        self.view.set_sensor_range(configured_range)
    def _clear_config(self):
        while self.config_form.count():
            item=self.config_form.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.config_widgets={}
    def _build_config(self, descriptor):
        if descriptor is None: self.config_box.hide(); return
        self.config_box.show()
        for field in descriptor.fields:
            if field.type == "boolean":
                widget=QCheckBox(); widget.setChecked(bool(field.default)); widget.setToolTip(field.description)
                self.config_form.addRow(field.label, widget); self.config_widgets[field.key]=widget
            elif field.type == "decimal" and field.minimum is not None and field.maximum is not None:
                slider=QSlider(Qt.Horizontal); slider.setRange(round(field.minimum*100), round(field.maximum*100)); slider.setValue(round(float(field.default or 0)*100)); slider.setToolTip(field.description)
                label=QLabel(f"{float(field.default or 0):.2f}"); row=QHBoxLayout(); row.addWidget(slider,1); row.addWidget(label)
                holder=QWidget(); holder.setLayout(row); self.config_form.addRow(field.label,holder); self.config_widgets[field.key]=(slider,label)
                slider.valueChanged.connect(lambda value, out=label: out.setText(f"{value/100:.2f}"))
        enabled=self.config_widgets.get("noise_enabled"); level=self.config_widgets.get("noise_level")
        if isinstance(enabled,QCheckBox) and isinstance(level,tuple):
            def toggle_noise(checked):
                if checked and level[0].value() == 0:
                    level[0].setValue(25)
                level[0].setEnabled(checked)
                if self.controller: self.start()
            level[0].setEnabled(enabled.isChecked()); enabled.toggled.connect(toggle_noise)
            level[0].sliderReleased.connect(self._configuration_changed)
    def _configuration_changed(self):
        if self.controller: self.start()
    def _source_config(self):
        return {key: widget.isChecked() if isinstance(widget,QCheckBox) else widget[0].value()/100 for key,widget in self.config_widgets.items()}
    def start(self):
        if self.controller: self.stop()
        if self.providers.currentIndex()<0: self._set_health("No drivers installed"); return
        provider=self.providers.currentData(); descriptor=self.sources.currentData()
        if provider is None or descriptor is None:
            self._set_health("No driver/source available. Install a driver and restart.")
            return
        source=provider.create_source(descriptor.source_id,provider.validate_config(descriptor.source_id,self._source_config()))
        self._apply_source_range()
        self._stream_text=""
        self.controller=AcquisitionController(source); self.controller.scan_received.connect(self._scan_received); self.controller.status.connect(self._source_status); self.controller.failure.connect(self._acquisition_failure); self.controller.start(); self.start_button.setEnabled(False); self.stop_button.setEnabled(True); self._set_health("Waiting for data…")
    def _acquisition_failure(self,error):
        self.start_button.setEnabled(True); self.stop_button.setEnabled(False); self._set_health(f"Acquisition error: {error}")
    def _scan_received(self,scan):
        self.view.set_scan(scan)
        valid=sum(1 for s in scan.sample_status if s.value == 'VALID'); self._last_counts=(valid, scan.sample_count)
        self._selected_point=None
        self._mouse_position_changed(self._mouse_position)
        self._health_text=""
        self._mouse_position_changed(self._mouse_position)
    def _source_status(self,source_status):
        rate='—' if source_status.scan_rate_hz is None else f"{source_status.scan_rate_hz:.1f} Hz"
        drops=dict(source_status.counters).get('consumer_drops', dict(source_status.counters).get('drops', 0))
        age='—' if source_status.latest_scan_age_s is None else f"{source_status.latest_scan_age_s:.2f} s"
        valid,total=self._last_counts
        self._stream_text=f"{rate} · latest {age} · {valid}/{total} valid · drops {drops}"
        self._mouse_position_changed(self._mouse_position)
    def stop(self):
        if self.controller:
            controller=self.controller; self.controller=None
            try: controller.stop()
            except Exception as exc: self._set_health(f"Stop error: {exc}")
        self.start_button.setEnabled(True); self.stop_button.setEnabled(False)
        self.view.clear_scan()
        self._last_counts=(0, 0); self._selected_point=None; self._stream_text=""; self._mouse_position_changed(self._mouse_position)
        if not self._health_text.startswith("Stop error"): self._set_health("Stopped · canvas cleared")
    def closeEvent(self,event): self.stop(); event.accept()
def main():
    app=QApplication(sys.argv)
    icon_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
    if not icon_path.is_file():
        icon_path = Path(sys.prefix) / "share" / "lidar-shark" / "logo.png"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    window=MainWindow(); window.show(); return app.exec()
if __name__=="__main__": main()
