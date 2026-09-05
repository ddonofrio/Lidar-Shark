import math
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPen, QPainter
from PySide6.QtWidgets import QWidget
from lidar_sdk.geometry import scan_to_points

class ScanView(QWidget):
    sample_selected=Signal(object)
    def __init__(self,parent=None):
        super().__init__(parent); self.scan=None; self.zoom=1.0; self.setMinimumSize(500,400)
    def set_scan(self,scan): self.scan=scan; self.update()
    def _point(self,p):
        scale=min(self.width(),self.height())/12000*self.zoom
        return self.width()/2-p.y_mm*scale, self.height()/2-p.x_mm*scale
    def paintEvent(self,event):
        painter=QPainter(self); painter.fillRect(self.rect(),QBrush(QColor("#10151c"))); painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#35404c"),1)); c=self.rect().center(); painter.drawLine(0,c.y(),self.width(),c.y()); painter.drawLine(c.x(),0,c.x(),self.height())
        painter.setPen(QPen(QColor("#6ee7b7"),3));
        if self.scan:
            for p in scan_to_points(self.scan): painter.drawPoint(*self._point(p))
        painter.setPen(QPen(QColor("#f87171"),2)); painter.drawLine(c.x(),c.y(),c.x(),c.y()-35)
    def mousePressEvent(self,event):
        if not self.scan: return
        candidates=[]
        for p in scan_to_points(self.scan):
            x,y=self._point(p); d=math.hypot(x-event.position().x(),y-event.position().y())
            if d<=8: candidates.append((d,p.sample_index,p))
        if candidates: self.sample_selected.emit(min(candidates,key=lambda x:(x[0],x[1]))[2])
    def wheelEvent(self,event): self.zoom=max(.1,min(10,self.zoom*(1.1 if event.angleDelta().y()>0 else .9))); self.update()
