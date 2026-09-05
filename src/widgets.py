import math
import time
from PySide6.QtCore import Qt, Signal, QPointF, QLineF
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QFont, QCursor
from PySide6.QtWidgets import QWidget
from lidar_sdk.geometry import scan_to_points

class ScanView(QWidget):
    sample_selected=Signal(object)
    # Emits lidar-frame coordinates as (angle in degrees, distance in mm).
    mouse_position_changed=Signal(object)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.scan=None; self.zoom=1.0; self._returns=[]; self.persistence_s=0.75; self.color_mode="Uniform"; self.sensor_range_mm=None
        self.pan_x=0.0; self.pan_y=0.0; self.selected_point=None; self._drag_start=None; self._pan_start=(0.0, 0.0); self._was_drag=False
        self.setMinimumSize(500,400)
        self.setMouseTracking(True)
        self._timer = self.startTimer(33)
    def set_persistence(self, value):
        self.persistence_s = value / 1000.0
        self.update()
    def set_color_mode(self, mode):
        self.color_mode=mode
        self.update()
    def set_sensor_range(self, range_mm):
        self.sensor_range_mm=float(range_mm) if range_mm and range_mm > 0 else None
        self.update()
    def clear_scan(self):
        self.scan=None; self.selected_point=None; self._returns.clear(); self.update()
    def recenter(self):
        self.pan_x=0.0; self.pan_y=0.0; self.update()
    def set_scan(self,scan):
        now = time.monotonic()
        self.scan=scan
        self.selected_point=None
        self._returns.extend((p, now) for p in scan_to_points(scan))
        cutoff=now-self.persistence_s
        self._returns=[item for item in self._returns if item[1] >= cutoff]
        self.update()
    def timerEvent(self,event):
        cutoff=time.monotonic()-self.persistence_s
        self._returns=[item for item in self._returns if item[1] >= cutoff]
        self.update()
    def _point(self,p):
        range_mm=self.sensor_range_mm or 5000.0
        scale=min(self.width(),self.height())/(2*range_mm)*self.zoom
        return self.width()/2+self.pan_x-p.y_mm*scale, self.height()/2+self.pan_y-p.x_mm*scale
    def _scale(self):
        return min(self.width(),self.height())/(2*(self.sensor_range_mm or 5000.0))*self.zoom
    def _sensor_coordinates(self, position):
        """Convert a canvas position to the lidar's local X/Y coordinates."""
        scale=self._scale(); origin_x=self.width()/2+self.pan_x; origin_y=self.height()/2+self.pan_y
        x=(origin_y-position.y())/scale
        y=(origin_x-position.x())/scale
        return x, y
    def _emit_mouse_position(self, position):
        x, y=self._sensor_coordinates(position)
        distance=math.hypot(x,y)
        angle=math.degrees(math.atan2(y,x)) % 360.0
        self.mouse_position_changed.emit((angle, distance))
    def paintEvent(self,event):
        painter=QPainter(self); painter.fillRect(self.rect(),QBrush(QColor("#08110e"))); painter.setRenderHint(QPainter.Antialiasing)
        c=QPointF(self.width()/2+self.pan_x, self.height()/2+self.pan_y); range_mm=self.sensor_range_mm
        scale=min(self.width(),self.height())/(2*(range_mm or 5000.0))*self.zoom
        # One-metre range rings, deliberately subtle so returns remain dominant.
        painter.setPen(QPen(QColor(47,82,70,55),1))
        if range_mm:
            for metres in range(1, int(range_mm//1000)+1):
                painter.drawEllipse(c, int(metres*1000*scale), int(metres*1000*scale))
        painter.setPen(QPen(QColor("#315447"),1)); painter.drawLine(QLineF(0,c.y(),self.width(),c.y())); painter.drawLine(QLineF(c.x(),0,c.x(),self.height()))
        now=time.monotonic()
        for p, born in self._returns:
            age=now-born; alpha=max(15,min(255,int(255*(1-age/max(self.persistence_s,0.001)))))
            if self.color_mode == "By range":
                distance=min(1.0, math.hypot(p.x_mm,p.y_mm)/(self.sensor_range_mm or 5000.0))
                point_color=QColor.fromHsvF(0.42-0.42*distance, 0.82, 0.95, alpha/255.0)
            else:
                point_color=QColor(80,230,170,alpha)
            painter.setPen(QPen(point_color,3)); painter.drawPoint(*self._point(p))
        if self.selected_point is not None:
            sx, sy=self._point(self.selected_point)
            painter.setPen(QPen(QColor("#ffd166"), 2)); painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(sx, sy), 7, 7)
            painter.drawLine(QLineF(c.x(), c.y(), sx, sy))
        painter.setFont(QFont("Segoe UI",9))
        # A compact physical reference, anchored to the lower-right corner.
        # Pick a round metric reference whose rendered length is stable and exact.
        if range_mm:
            bar_mm=1000
            for candidate in (500,1000,2000,5000):
                pixels=candidate*scale
                if 60 <= pixels <= 160:
                    bar_mm=candidate; break
            bar=max(30,int(bar_mm*scale))
            x=self.width()-bar-18; y=self.height()-30
            painter.setPen(QPen(QColor("#d7eee5"),2)); painter.drawLine(x,y,x+bar,y); painter.drawLine(x,y-5,x,y+5); painter.drawLine(x+bar,y-5,x+bar,y+5)
            painter.drawText(x, y-9, f"{bar_mm/1000:g} m")
    def mousePressEvent(self,event):
        if event.button() == Qt.LeftButton:
            self._drag_start=event.position(); self._pan_start=(self.pan_x,self.pan_y); self._was_drag=False
            self.setCursor(QCursor(Qt.ClosedHandCursor)); event.accept(); return
        super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        self._emit_mouse_position(event.position())
        if self._drag_start is not None and event.buttons() & Qt.LeftButton:
            delta=event.position()-self._drag_start
            if abs(delta.x()) + abs(delta.y()) >= 3: self._was_drag=True
            self.pan_x=self._pan_start[0]+delta.x(); self.pan_y=self._pan_start[1]+delta.y(); self.update()
        else:
            super().mouseMoveEvent(event)
    def mouseReleaseEvent(self,event):
        if event.button() == Qt.LeftButton:
            was_drag=self._was_drag; self._drag_start=None; self.setCursor(QCursor(Qt.ArrowCursor))
            if not was_drag and self.scan:
                candidates=[]
                for p in scan_to_points(self.scan):
                    x,y=self._point(p); d=math.hypot(x-event.position().x(),y-event.position().y())
                    if d<=8: candidates.append((d,p.sample_index,p))
                if candidates:
                    self.selected_point=min(candidates,key=lambda x:(x[0],x[1]))[2]
                    self.sample_selected.emit(self.selected_point); self.update()
            event.accept(); return
        super().mouseReleaseEvent(event)
    def leaveEvent(self,event):
        self.mouse_position_changed.emit(None); super().leaveEvent(event)
    def wheelEvent(self,event):
        self.zoom=max(.1,min(10,self.zoom*(1.1 if event.angleDelta().y()>0 else .9)))
        self._emit_mouse_position(event.position()); self.update()
