import math
import time
from PySide6.QtCore import Qt, Signal, QPointF, QLineF, QRectF
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QFont, QCursor, QFontMetrics
from PySide6.QtWidgets import QWidget
from lidar_sdk.geometry import scan_to_points

class ScanView(QWidget):
    sample_selected=Signal(object)
    # Emits lidar-frame coordinates as (angle in degrees, distance in mm).
    mouse_position_changed=Signal(object)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.scan=None; self.zoom=1.0; self._returns=[]; self.persistence_s=0.75; self.color_mode="Uniform"; self.sensor_range_mm=None
        self.pan_x=0.0; self.pan_y=0.0; self.selected_point=None; self.show_color_range=True; self.show_grid=True; self._drag_start=None; self._pan_start=(0.0, 0.0); self._was_drag=False
        self.setMinimumSize(500,400)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._timer = self.startTimer(33)
    def set_persistence(self, value):
        self.persistence_s = value / 1000.0
        self.update()
    def set_color_mode(self, mode):
        self.color_mode=mode
        self.update()
    def set_show_color_range(self, visible):
        self.show_color_range=bool(visible)
        self.update()
    def set_show_grid(self, visible):
        self.show_grid=bool(visible)
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
    def _range_color(self, distance_mm):
        if distance_mm <= 2000:
            return QColor("#39d353")
        if distance_mm <= 8000:
            return QColor("#ffd21f")
        return QColor("#ff3030")
    @staticmethod
    def _range_legend_segments():
        return (("#39d353", "0-2 m", "±15 mm"), ("#ffd21f", "2-8 m", "±20 mm"), ("#ff3030", "8-25 m", "±30 mm"))
    def _grid_spacing_mm(self, scale):
        target_pixels=70.0
        raw=target_pixels/scale
        power=10 ** math.floor(math.log10(max(raw, 1.0)))
        for multiplier in (1.0, 2.0, 5.0, 10.0):
            spacing=multiplier*power
            if spacing*scale >= target_pixels:
                return spacing
        return 10.0*power
    def paintEvent(self,event):
        painter=QPainter(self); painter.fillRect(self.rect(),QBrush(QColor("#08110e"))); painter.setRenderHint(QPainter.Antialiasing)
        c=QPointF(self.width()/2+self.pan_x, self.height()/2+self.pan_y); range_mm=self.sensor_range_mm
        display_range_mm=range_mm or 5000.0
        scale=min(self.width(),self.height())/(2*display_range_mm)*self.zoom
        if self.show_grid:
            # Adaptive metric grid; its spacing remains readable at every zoom level.
            grid_spacing=self._grid_spacing_mm(scale)
            grid_pen=QPen(QColor(47,82,70,38),1)
            painter.setPen(grid_pen)
            min_x=(c.y()-self.height())/scale; max_x=c.y()/scale
            min_y=(c.x()-self.width())/scale; max_y=c.x()/scale
            first_x=math.floor(min_x/grid_spacing)-1; last_x=math.ceil(max_x/grid_spacing)+1
            first_y=math.floor(min_y/grid_spacing)-1; last_y=math.ceil(max_y/grid_spacing)+1
            for index in range(first_x,last_x+1):
                x_mm=index*grid_spacing
                painter.drawLine(QLineF(0,c.y()-x_mm*scale,self.width(),c.y()-x_mm*scale))
            for index in range(first_y,last_y+1):
                y_mm=index*grid_spacing
                painter.drawLine(QLineF(c.x()-y_mm*scale,0,c.x()-y_mm*scale,self.height()))
            painter.setFont(QFont("Segoe UI",8)); painter.setPen(QPen(QColor(150,205,185,150),1))
            for index in range(first_x,last_x+1):
                x_mm=index*grid_spacing; screen_y=c.y()-x_mm*scale
                if 0 <= screen_y <= self.height(): painter.drawText(5,screen_y-3,f"{x_mm/1000:g} m")
            for index in range(first_y,last_y+1):
                y_mm=index*grid_spacing; screen_x=c.x()-y_mm*scale
                if 0 <= screen_x <= self.width(): painter.drawText(screen_x+4,self.height()-5,f"{y_mm/1000:g} m")
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
                point_distance=math.hypot(p.x_mm,p.y_mm)
                if point_distance > 25000:
                    continue
                point_color=self._range_color(point_distance); point_color.setAlpha(alpha)
            else:
                point_color=QColor(80,230,170,alpha)
            painter.setPen(QPen(point_color,3)); painter.drawPoint(*self._point(p))
        if self.selected_point is not None:
            sx, sy=self._point(self.selected_point)
            painter.setPen(QPen(QColor("#ffd166"), 2)); painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(sx, sy), 7, 7)
            painter.drawLine(QLineF(c.x(), c.y(), sx, sy))
        painter.setFont(QFont("Segoe UI",9))
        # Always show a compact physical reference in the lower-right corner.
        bar_mm=1000
        for candidate in (250,500,1000,2000,5000):
            pixels=candidate*scale
            if 60 <= pixels <= 160:
                bar_mm=candidate; break
        bar=max(30,int(bar_mm*scale))
        x=self.width()-bar-18; y=self.height()-30
        painter.setPen(QPen(QColor("#d7eee5"),2)); painter.drawLine(x,y,x+bar,y); painter.drawLine(x,y-5,x,y+5); painter.drawLine(x+bar,y-5,x+bar,y+5)
        painter.drawText(x, y-9, f"{bar_mm/1000:g} m")
        if self.color_mode == "By range" and self.show_color_range:
            legend_width=min(160, max(140, self.width()-bar-70)); legend_x=self.width()-legend_width-18; legend_y=18; legend_height=10
            segments=self._range_legend_segments()
            segment_width=legend_width/len(segments)
            for index,(color,_,_) in enumerate(segments):
                painter.fillRect(QRectF(legend_x+index*segment_width,legend_y,segment_width,legend_height),QBrush(QColor(color)))
            painter.setPen(QPen(QColor("#d7eee5"),1)); painter.drawRect(legend_x,legend_y,legend_width,legend_height)
            painter.setFont(QFont("Segoe UI",7))
            for index,(_,value_text,precision_text) in enumerate(segments):
                tick_x=legend_x+(index+0.5)*segment_width
                painter.drawLine(tick_x,legend_y+legend_height,tick_x,legend_y+legend_height+4)
                metrics=QFontMetrics(painter.font())
                value_x=max(legend_x,min(tick_x-metrics.horizontalAdvance(value_text)//2,legend_x+legend_width-metrics.horizontalAdvance(value_text)))
                painter.drawText(value_x,legend_y+legend_height+15,value_text)
                precision_x=max(legend_x,min(tick_x-metrics.horizontalAdvance(precision_text)//2,legend_x+legend_width-metrics.horizontalAdvance(precision_text)))
                painter.drawText(precision_x,legend_y+legend_height+28,precision_text)
            painter.drawText(legend_x,legend_y-4,"Range")
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
        self.setFocus(Qt.MouseFocusReason)
        delta=event.angleDelta().y() or event.pixelDelta().y()
        if delta == 0:
            event.ignore(); return
        self.zoom=max(.1,min(10,self.zoom*(1.1 if delta>0 else .9)))
        self._emit_mouse_position(event.position()); self.update()
        event.accept()
