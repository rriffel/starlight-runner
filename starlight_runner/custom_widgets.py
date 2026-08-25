"""
custom_widgets.py — Custom PyQt5 widgets for Starlight Runner GUI.
Includes dual-handle range sliders, collapsible panels, and plotting canvas wrappers.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
    QToolButton, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPropertyAnimation, QParallelAnimationGroup, QAbstractAnimation
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont


class DoubleSlider(QWidget):
    """
    A custom double-handled graphical range slider with smooth handle drag.
    """
    rangeChanged = pyqtSignal(float, float)

    def __init__(self, min_val=3000.0, max_val=10000.0, step=10.0, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(28)
        self.setMinimumWidth(120)
        
        self._min = float(min_val)
        self._max = float(max_val)
        self._step = float(step)
        
        self._low = float(min_val)
        self._high = float(max_val)
        
        self._handle_radius = 8
        self._track_height = 6
        self._active_handle = None  # 0 for low, 1 for high
        
        self.setMouseTracking(True)
        
    def get_range(self):
        return self._low, self._high
        
    def set_range(self, low, high):
        self._low = max(self._min, min(float(low), self._max))
        self._high = max(self._min, min(float(high), self._max))
        if self._low > self._high:
            self._low, self._high = self._high, self._low
        self.update()
        
    def set_bounds(self, min_val, max_val):
        self._min = float(min_val)
        self._max = float(max_val)
        self.set_range(self._low, self._high)
        self.update()

    def _val_to_x(self, val):
        usable_width = self.width() - 2 * self._handle_radius
        if self._max == self._min:
            return self._handle_radius
        fraction = (val - self._min) / (self._max - self._min)
        return self._handle_radius + fraction * usable_width

    def _x_to_val(self, x):
        usable_width = self.width() - 2 * self._handle_radius
        if usable_width <= 0:
            return self._min
        fraction = max(0.0, min(1.0, (x - self._handle_radius) / usable_width))
        raw_val = self._min + fraction * (self._max - self._min)
        if self._step > 0:
            return round(raw_val / self._step) * self._step
        return raw_val

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        y_center = self.height() / 2.0
        x_low = self._val_to_x(self._low)
        x_high = self._val_to_x(self._high)
        
        # Draw background track
        track_rect = QRectF(
            self._handle_radius,
            y_center - self._track_height / 2.0,
            self.width() - 2 * self._handle_radius,
            self._track_height
        )
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#E2E8F0")))
        painter.drawRoundedRect(track_rect, self._track_height / 2.0, self._track_height / 2.0)
        
        # Draw active highlighted track between handles
        active_rect = QRectF(
            x_low,
            y_center - self._track_height / 2.0,
            max(0.0, x_high - x_low),
            self._track_height
        )
        painter.setBrush(QBrush(QColor("#2563EB")))
        painter.drawRoundedRect(active_rect, self._track_height / 2.0, self._track_height / 2.0)
        
        # Draw Low Handle
        painter.setPen(QPen(QColor("#1D4ED8"), 2))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QRectF(
            x_low - self._handle_radius,
            y_center - self._handle_radius,
            self._handle_radius * 2,
            self._handle_radius * 2
        ))
        
        # Draw High Handle
        painter.drawEllipse(QRectF(
            x_high - self._handle_radius,
            y_center - self._handle_radius,
            self._handle_radius * 2,
            self._handle_radius * 2
        ))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.x()
            x_low = self._val_to_x(self._low)
            x_high = self._val_to_x(self._high)
            
            d_low = abs(x - x_low)
            d_high = abs(x - x_high)
            
            if d_low < d_high:
                self._active_handle = 0
                self._low = self._x_to_val(x)
            else:
                self._active_handle = 1
                self._high = self._x_to_val(x)
                
            if self._low > self._high:
                self._low, self._high = self._high, self._low
                self._active_handle = 1 - self._active_handle
                
            self.update()
            self.rangeChanged.emit(self._low, self._high)

    def mouseMoveEvent(self, event):
        if self._active_handle is not None and (event.buttons() & Qt.LeftButton):
            val = self._x_to_val(event.x())
            if self._active_handle == 0:
                self._low = min(val, self._high)
            else:
                self._high = max(val, self._low)
            self.update()
            self.rangeChanged.emit(self._low, self._high)

    def mouseReleaseEvent(self, event):
        self._active_handle = None


class VisualRangeSlider(QWidget):
    """
    Combined Widget with Min/Max value readout labels and DoubleSlider.
    """
    rangeChanged = pyqtSignal(float, float)

    def __init__(self, title="Wavelength Range", min_val=3000.0, max_val=10000.0, step=10.0, unit="Å", parent=None):
        super().__init__(parent)
        self.unit = unit
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        header = QHBoxLayout()
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-weight: 600; color: #334155;")
        self.lbl_values = QLabel(f"{min_val:.0f} - {max_val:.0f} {unit}")
        self.lbl_values.setStyleSheet("color: #2563EB; font-weight: 600;")
        
        header.addWidget(self.lbl_title)
        header.addStretch()
        header.addWidget(self.lbl_values)
        layout.addLayout(header)
        
        self.slider = DoubleSlider(min_val, max_val, step, self)
        self.slider.rangeChanged.connect(self._on_change)
        layout.addWidget(self.slider)

    def _on_change(self, low, high):
        self.lbl_values.setText(f"{low:.0f} - {high:.0f} {self.unit}")
        self.rangeChanged.emit(low, high)

    def set_range(self, low, high):
        self.slider.set_range(low, high)
        self.lbl_values.setText(f"{low:.0f} - {high:.0f} {self.unit}")

    def get_range(self):
        return self.slider.get_range()


class CollapsibleBox(QWidget):
    """
    A custom collapsible group box with smooth toggle animation.
    """
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.toggle_button = QToolButton(self)
        self.toggle_button.setStyleSheet("""
            QToolButton {
                border: none;
                font-weight: bold;
                font-size: 13px;
                color: #1E293B;
                background-color: transparent;
                padding: 6px;
            }
            QToolButton:hover {
                color: #2563EB;
            }
        """)
        self.toggle_button.setText(f"▼  {title}")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.clicked.connect(self.on_toggle)

        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(8, 8, 8, 8)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)

        self._title = title

    def on_toggle(self, checked):
        if checked:
            self.toggle_button.setText(f"▼  {self._title}")
            self.content_area.setVisible(True)
        else:
            self.toggle_button.setText(f"▶  {self._title}")
            self.content_area.setVisible(False)

    def setContentLayout(self, layout):
        # Clear existing
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.content_layout.addLayout(layout)
