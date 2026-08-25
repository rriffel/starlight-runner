"""
custom_widgets.py — Custom PyQt5 widgets for Starlight Runner GUI.
Includes dual-handle range sliders, collapsible panels, and plotting canvas wrappers.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os
import sys
import subprocess
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from .masking import SpectralMask
from .gui.constants import STYLESHEET


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

class RangeTableWidget(QWidget):
    def __init__(self, data_dict):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Label", "Min Age", "Max Age"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("+ Add Row")
        btn_add.clicked.connect(self._add_row)
        btn_del = QPushButton("- Remove Row")
        btn_del.clicked.connect(self._remove_row)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        self.layout.addLayout(btn_layout)
        
        self.load_data(data_dict)
        
    def _add_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem("New"))
        self.table.setItem(r, 1, QTableWidgetItem("0"))
        self.table.setItem(r, 2, QTableWidgetItem("1e9"))
        
    def _remove_row(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
            
    def load_data(self, d):
        self.table.setRowCount(len(d))
        for r, (k, v) in enumerate(d.items()):
            self.table.setItem(r, 0, QTableWidgetItem(str(k)))
            self.table.setItem(r, 1, QTableWidgetItem(str(v[0])))
            self.table.setItem(r, 2, QTableWidgetItem(str(v[1])))
            
    def get_data(self):
        d = {}
        for r in range(self.table.rowCount()):
            if not self.table.item(r, 0): continue
            k = self.table.item(r, 0).text()
            try:
                v1 = float(self.table.item(r, 1).text())
                v2 = float(self.table.item(r, 2).text())
                d[k] = [v1, v2]
            except:
                pass
        return d

class PylightConfigDialog(QDialog):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.setWindowTitle("Pylight Configuration Editor")
        self.resize(600, 450)
        self.config = config.copy()
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        # General Tab
        tab_gen = QWidget()
        form = QFormLayout(tab_gen)
        
        self.le_zs = QLineEdit(", ".join(map(str, self.config.get("Zs", []))))
        form.addRow("Metallicities (Zs) [comma separated]:", self.le_zs)
        
        self.chk_agn = QCheckBox()
        self.chk_agn.setChecked(self.config.get("IsAGNComp", True))
        form.addRow("Is AGN Component:", self.chk_agn)
        
        self.chk_onlyfc = QCheckBox()
        self.chk_onlyfc.setChecked(self.config.get("OnlyFC", False))
        form.addRow("Only FC:", self.chk_onlyfc)
        
        self.chk_pltmask = QCheckBox()
        self.chk_pltmask.setChecked(self.config.get("pltmask", False))
        form.addRow("Plot Masked & Clipped Points:", self.chk_pltmask)
        
        self.sb_normfac = QDoubleSpinBox()
        self.sb_normfac.setRange(0, 1e9)
        self.sb_normfac.setDecimals(4)
        self.sb_normfac.setValue(self.config.get("NormFac", 1.0))
        form.addRow("Normalization Factor:", self.sb_normfac)
        
        self.sb_zsun = QDoubleSpinBox()
        self.sb_zsun.setDecimals(5)
        self.sb_zsun.setSingleStep(0.001)
        self.sb_zsun.setValue(self.config.get("zsun", 0.0152))
        form.addRow("Z_sun:", self.sb_zsun)
        
        tabs.addTab(tab_gen, "General")
        
        # Bins Tabs
        self.tbl_pop = RangeTableWidget(self.config.get("BinPopVec", {}))
        tabs.addTab(self.tbl_pop, "Pop Vectors (BinPopVec)")
        
        self.tbl_sfr = RangeTableWidget(self.config.get("BinSFR", {}))
        tabs.addTab(self.tbl_sfr, "SFR (BinSFR)")
        
        self.tbl_hd = RangeTableWidget(self.config.get("BinHDVec", {}))
        tabs.addTab(self.tbl_hd, "Hot Dust (BinHDVec)")
        
        self.tbl_fc = RangeTableWidget(self.config.get("BinFCVec", {}))
        tabs.addTab(self.tbl_fc, "Featureless (BinFCVec)")
        
        main_layout.addWidget(tabs)

        btn_box = QHBoxLayout()
        btn_save = QPushButton("Save && Update Plots")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        main_layout.addLayout(btn_box)

    def _save(self):
        try:
            zs_str = self.le_zs.text().replace(' ', '')
            self.config["Zs"] = [float(x) for x in zs_str.split(',') if x]
            self.config["IsAGNComp"] = self.chk_agn.isChecked()
            self.config["OnlyFC"] = self.chk_onlyfc.isChecked()
            self.config["pltmask"] = self.chk_pltmask.isChecked()
            self.config["NormFac"] = self.sb_normfac.value()
            self.config["zsun"] = self.sb_zsun.value()
            
            self.config["BinPopVec"] = self.tbl_pop.get_data()
            self.config["BinSFR"] = self.tbl_sfr.get_data()
            self.config["BinHDVec"] = self.tbl_hd.get_data()
            self.config["BinFCVec"] = self.tbl_fc.get_data()
            
            self.config["BinPopVecLab"] = list(self.config["BinPopVec"].keys())
            self.config["BinSFRLabs"] = list(self.config["BinSFR"].keys())
            self.config["BinHDVecLab"] = list(self.config["BinHDVec"].keys())
            self.config["BinFCVecLab"] = list(self.config["BinFCVec"].keys())
            
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Invalid Format", f"Error parsing input: {str(e)}")


class StarlightWorkerThread(QThread):
    """
    Background worker thread for running Starlight grid batch.
    """
    grid_finished = pyqtSignal(dict)
    all_finished = pyqtSignal()
    log_message = pyqtSignal(str)

    def __init__(self, grid_files, starlight_exe, cwd="."):
        super().__init__()
        self.grid_files = grid_files
        self.starlight_exe = starlight_exe
        self.cwd = cwd
        self._is_cancelled = False

    def run(self):
        import subprocess
        total = len(self.grid_files)
        self.log_message.emit(f"🚀 Starting STARLIGHT execution on {total} grid file(s)...")

        for idx, g in enumerate(self.grid_files, 1):
            if self._is_cancelled:
                self.log_message.emit("⚠️ Batch execution cancelled by user.")
                break

            self.log_message.emit(f"[{idx}/{total}] Running grid: {os.path.basename(g)}...")
            
            exe_path = os.path.abspath(os.path.join(self.cwd, self.starlight_exe)) if not os.path.isabs(self.starlight_exe) else self.starlight_exe
            if not os.path.exists(exe_path):
                exe_path = self.starlight_exe

            with open(g, 'r') as grid_in:
                process = subprocess.Popen(
                    [exe_path],
                    stdin=grid_in,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=self.cwd,
                    text=True,
                    bufsize=1
                )
                
                # Stream output line by line
                for line in process.stdout:
                    if self._is_cancelled:
                        process.terminate()
                        break
                    # Emit line without trailing newline since append() adds one
                    self.log_message.emit(line.rstrip('\n'))
                
                process.wait()
                
            res = {"grid": g, "returncode": process.returncode}
            self.grid_finished.emit(res)
            
            if process.returncode == 0:
                self.log_message.emit(f"✅ Finished: {os.path.basename(g)}\n")
            else:
                self.log_message.emit(f"❌ Error in {os.path.basename(g)} (code {process.returncode})\n")

        self.all_finished.emit()


class InteractiveMaskDialog(QDialog):
    """
    Dedicated Detached/Pop-out Interactive Masking Studio (CreateMasks Mode).
    Opens full-screen / maximized.
    Provides fast, dedicated 2-point clicking:
      - Right-click: mask with weight 0.0 (red)
      - Middle-click: mask with weight 2.0 (green)
      - Left-click: mask with selected weight / zoom
      - Key 'd': hover and delete
      - Key 'q' / 'Esc' or button: complete & close, syncing back to main window.
    """
    def __init__(self, parent, wl, flux, eflux, spectral_mask, spectrum_path=None, mask_dir=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("STARLIGHT — Interactive Mask Studio (CreateMasks Mode)")
        self.resize(1300, 850)
        self.setStyleSheet(STYLESHEET)

        self.wl = wl
        self.flux = flux
        self.eflux = eflux
        self.spectral_mask = spectral_mask
        self.spectrum_path = spectrum_path
        self.click_pt = None
        self.click_weight = 0.0

        # Derive default mask filename: <spec_base>.sm
        mask_ext = getattr(parent, 'starlight_config', None)
        mask_ext = mask_ext.mask_ext if mask_ext else ".mask"
        if not mask_ext.startswith('.'): mask_ext = "." + mask_ext
        
        if self.spectrum_path:
            spec_base = os.path.splitext(os.path.basename(self.spectrum_path))[0]
            if mask_dir:
                self.default_mask_path = os.path.join(mask_dir, f"{spec_base}{mask_ext}")
            else:
                spec_dir = os.path.dirname(self.spectrum_path)
                self.default_mask_path = os.path.join(spec_dir, f"{spec_base}{mask_ext}") if spec_dir else f"{spec_base}{mask_ext}"
        else:
            if mask_dir:
                self.default_mask_path = os.path.join(mask_dir, f"mask{mask_ext}")
            else:
                self.default_mask_path = f"mask{mask_ext}"

        self._init_ui()
        self._plot()


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Top Bar
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        top_layout.addWidget(QLabel("<b>Left Click:</b>"))
        self.rb_w0 = QRadioButton("Weight 0.0 (Red - Exclude)")
        self.rb_w0.setChecked(True)
        self.rb_w2 = QRadioButton("Weight 2.0 (Green - Emphasize)")
        top_layout.addWidget(self.rb_w0)
        top_layout.addWidget(self.rb_w2)

        btn_opt = QPushButton("Optical Preset (CreateMasks)")
        btn_opt.clicked.connect(self._apply_optical)
        top_layout.addWidget(btn_opt)

        btn_nir = QPushButton("NIR Preset")
        btn_nir.clicked.connect(self._apply_nir)
        top_layout.addWidget(btn_nir)

        btn_load_sm = QPushButton("Load .mask")
        btn_load_sm.setStyleSheet("background-color: #2563EB; color: white; font-weight: 600;")
        btn_load_sm.clicked.connect(self._on_load_sm)
        top_layout.addWidget(btn_load_sm)

        btn_save_sm = QPushButton("Save .mask")
        btn_save_sm.clicked.connect(self._on_save_sm)
        top_layout.addWidget(btn_save_sm)

        btn_clear = QPushButton("Clear All")
        btn_clear.setStyleSheet("background-color: #EF4444; color: white;")
        btn_clear.clicked.connect(self._clear_all)
        top_layout.addWidget(btn_clear)

        top_layout.addStretch()

        btn_finish = QPushButton("✓ Finish Editing (or 'q' key)")
        btn_finish.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; font-size: 13px; padding: 6px 16px;")
        btn_finish.clicked.connect(self.accept)
        top_layout.addWidget(btn_finish)


        main_layout.addWidget(top_bar)

        # Instruction banner
        info_banner = QLabel(
            "<b>Botão Direito (Right-Click)</b>: 1º e 2º clique marca Peso 0.0 (Vermelho)  |  "
            "<b>Botão do Meio (Middle-Click)</b>: 1º e 2º clique marca Peso 2.0 (Verde)  |  "
            "<b>Tecla 'd'</b>: Apaga a região sob o cursor  |  "
            "<b>Tecla 'q' ou 'Esc'</b>: Conclui e fecha a janela"
        )
        info_banner.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 10px; color: #334155; font-size: 12px;")
        main_layout.addWidget(info_banner)

        # Horizontal Splitter: Table (left) + Large Plot (right)
        splitter = QSplitter(Qt.Horizontal)

        tbl_container = QWidget()
        tbl_layout = QVBoxLayout(tbl_container)
        tbl_layout.setContentsMargins(0, 0, 0, 0)
        tbl_layout.setSpacing(6)

        tbl_title = QLabel("Masked Regions")
        tbl_title.setStyleSheet("font-weight: bold; color: #1E293B; font-size: 12px;")
        tbl_layout.addWidget(tbl_title)

        self.tbl_masks = QTableWidget(0, 3)
        self.tbl_masks.setHorizontalHeaderLabels(["Low (A)", "Upp (A)", "Weight"])
        self.tbl_masks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_masks.setMinimumWidth(230)
        self.tbl_masks.setMaximumWidth(320)
        tbl_layout.addWidget(self.tbl_masks, 1)

        btn_del = QPushButton("Remove Selected")
        btn_del.clicked.connect(self._remove_selected)
        tbl_layout.addWidget(btn_del)

        splitter.addWidget(tbl_container)

        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(4)

        self.fig = Figure(figsize=(10, 7), tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.canvas.mpl_connect('button_press_event', self._on_canvas_click)
        self.canvas.mpl_connect('key_press_event', self._on_key_press)

        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas, 1)

        splitter.addWidget(plot_container)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, 1)

        self.lbl_status = QLabel("Ready to mask. Click on line extremes or use right-click.")
        self.lbl_status.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 500;")
        main_layout.addWidget(self.lbl_status)

        self._update_table()

    def _apply_optical(self):
        wl_range = (self.wl[0], self.wl[-1]) if self.wl is not None and len(self.wl) > 0 else None
        self.spectral_mask = SpectralMask.from_preset("optical", wl_range=wl_range)
        self._update_table()
        self._plot()

    def _apply_nir(self):
        wl_range = (self.wl[0], self.wl[-1]) if self.wl is not None and len(self.wl) > 0 else None
        self.spectral_mask = SpectralMask.from_preset("nir", wl_range=wl_range)
        self._update_table()
        self._plot()

    def _clear_all(self):
        self.spectral_mask.clear()
        self.click_pt = None
        self._update_table()
        self._plot()

    def _on_load_sm(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Mask File (.mask)", "", "Starlight Mask (*.mask);;All Files (*)"
        )
        if filepath:
            try:
                loaded = SpectralMask.from_file(filepath)
                self.spectral_mask = loaded
                self.click_pt = None
                self._update_table()
                self._plot(preserve_limits=True)
                self.lbl_status.setText(f"Mask loaded from {os.path.basename(filepath)} ({len(self.spectral_mask.intervals)} intervalos).")
            except Exception as e:
                QMessageBox.critical(self, "Error loading mask", str(e))

    def _on_save_sm(self):
        default_name = getattr(self, 'default_mask_path', 'mask.mask')
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save STARLIGHT Mask", default_name, "Starlight Mask (*.mask);;All Files (*)"
        )
        if filepath:
            try:
                self.spectral_mask.save_to_file(filepath)
                self.lbl_status.setText(f"Mask saved to {os.path.basename(filepath)}.")
                QMessageBox.information(self, "Mask Saved", f"Mask file successfully saved:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error saving mask", str(e))

    def accept(self):
        # Automatically persist mask with spectrum name upon concluding
        if hasattr(self, 'default_mask_path') and self.default_mask_path and len(self.spectral_mask.intervals) > 0:
            try:
                self.spectral_mask.save_to_file(self.default_mask_path)
            except Exception:
                pass
        super().accept()



    def _remove_selected(self):
        row = self.tbl_masks.currentRow()
        if 0 <= row < len(self.spectral_mask.intervals):
            self.spectral_mask.remove_interval(row)
            self._update_table()
            self._plot()

    def _update_table(self):
        self.tbl_masks.setRowCount(len(self.spectral_mask.intervals))
        for r, it in enumerate(self.spectral_mask.intervals):
            self.tbl_masks.setItem(r, 0, QTableWidgetItem(f"{it['low']:.1f}"))
            self.tbl_masks.setItem(r, 1, QTableWidgetItem(f"{it['upp']:.1f}"))
            self.tbl_masks.setItem(r, 2, QTableWidgetItem(f"{it['weight']:.1f}"))

    def _on_canvas_click(self, event):
        if event.inaxes != self.ax or event.xdata is None:
            return
        if self.toolbar.mode != '' and event.button not in (2, 3):
            return

        clicked_x = float(event.xdata)
        if event.button == 3:
            weight = 0.0
        elif event.button == 2:
            weight = 2.0
        else:
            weight = 0.0 if self.rb_w0.isChecked() else 2.0

        if self.click_pt is None:
            self.click_pt = clicked_x
            self.click_weight = weight
            w_txt = "0.0 (Exclude)" if weight == 0.0 else "2.0 (Emphasize)"
            self.lbl_status.setText(f"1st Point: {clicked_x:.1f} A. Click 2nd point to apply mask with weight {w_txt}.")
            self._plot()
        else:
            p1 = float(min(self.click_pt, clicked_x))
            p2 = float(max(self.click_pt, clicked_x))
            w = self.click_weight
            if (p2 - p1) > 1.0:
                name = "Mask (Weight 0)" if w == 0.0 else "Key Feature (Weight 2)"
                self.spectral_mask.add_interval(p1, p2, weight=w, name=name)
                self.lbl_status.setText(f"Region added: {p1:.1f} - {p2:.1f} A (peso={w:.1f})")
            self.click_pt = None
            self._update_table()
            self._plot()

    def _on_key_press(self, event):
        if event.key in ('q',):
            self.accept()
        elif event.key in ('escape',):
            if self.click_pt is not None:
                self.click_pt = None
                self._plot()
                self.lbl_status.setText("Selection canceled.")
            else:
                self.accept()
        elif event.key == 'd' and event.xdata is not None:
            x = float(event.xdata)
            to_remove = [i for i, it in enumerate(self.spectral_mask.intervals) if it["low"] <= x <= it["upp"]]
            if to_remove:
                for idx in reversed(to_remove):
                    self.spectral_mask.remove_interval(idx)
                self._update_table()
                self._plot()
                self.lbl_status.setText(f"Mask removed at {x:.1f} A.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            self.accept()
        elif event.key() == Qt.Key_Escape:
            if self.click_pt is not None:
                self.click_pt = None
                self._plot()
            else:
                self.accept()
        else:
            super().keyPressEvent(event)

    def _plot(self, preserve_limits=True):
        cur_xlim = self.ax.get_xlim() if preserve_limits and len(self.ax.lines) > 0 else None
        cur_ylim = self.ax.get_ylim() if preserve_limits and len(self.ax.lines) > 0 else None

        self.ax.cla()
        ax = self.ax
        wl, flx, eflx = self.wl, self.flux, self.eflux

        if wl is not None and flx is not None:
            ax.plot(wl, flx, color="#0F172A", lw=1.2, label="Spectrum")
            if eflx is not None and len(eflx) == len(wl):
                ax.fill_between(wl, flx - eflx, flx + eflx, color="#93C5FD", alpha=0.3, label=r"Error ($\pm 1\sigma$)")

            for idx, it in enumerate(self.spectral_mask.intervals):
                is_zero = (it["weight"] == 0.0)
                color = "#EF4444" if is_zero else "#10B981"
                alpha = 0.25 if is_zero else 0.20
                hatch = "//" if is_zero else None

                ax.axvspan(it["low"], it["upp"], color=color, alpha=alpha, hatch=hatch)
                mask_pts = (wl >= it["low"]) & (wl <= it["upp"])
                if np.any(mask_pts):
                    lbl = ("Weight 0 (Masked)" if is_zero else "Weight 2 (Feature)") if (idx == 0 or idx == 1) else None
                    ax.plot(wl[mask_pts], flx[mask_pts], color=color, lw=2.2, label=lbl)

            if self.click_pt is not None:
                ax.axvline(self.click_pt, color="#DC2626", linestyle="--", lw=2, label=f"1st Point: {self.click_pt:.1f} A")

            ax.legend(loc="upper right", frameon=True)

        ax.set_xlabel(r"Wavelength ($\AA$)", fontsize=12)
        ax.set_ylabel("Flux", fontsize=12)
        ax.set_title("Interactive Mask Studio (CreateMasks Mode: Red = Weight 0, Green = Weight 2)", fontsize=13, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.5)

        if cur_xlim is not None and cur_xlim != (0.0, 1.0) and cur_ylim is not None and cur_ylim != (0.0, 1.0):
            ax.set_xlim(cur_xlim)
            ax.set_ylim(cur_ylim)
        else:
            if wl is not None and len(wl) > 1:
                ax.set_xlim(wl[0], wl[-1])
            self.toolbar.update()

        self.canvas.draw_idle()




class InteractiveCutDialog(QDialog):
    """
    Dedicated Pop-out / Detached Window for Spectral Extremity & Telluric Cutting.
    """
    def __init__(self, parent, raw_wl, raw_flux, raw_eflux, telluric_cuts):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("STARLIGHT — Interactive Trimming (Telluric / Extremities)")
        self.resize(1300, 800)
        self.setStyleSheet(STYLESHEET)

        self.raw_wl = raw_wl
        self.raw_flux = raw_flux
        self.raw_eflux = raw_eflux
        self.telluric_cuts = telluric_cuts
        self.click_pt = None

        self._init_ui()
        self._plot()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        top_layout.addWidget(QLabel("<b>Interactive Spectrum Trimming:</b>"))
        
        btn_clear = QPushButton("Clear Cuts")
        btn_clear.setStyleSheet("background-color: #EF4444; color: white;")
        btn_clear.clicked.connect(self._clear_cuts)
        top_layout.addWidget(btn_clear)

        top_layout.addStretch()

        btn_finish = QPushButton("✓ Finish and Close (or 'q' key)")
        btn_finish.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; font-size: 13px; padding: 6px 16px;")
        btn_finish.clicked.connect(self.accept)
        top_layout.addWidget(btn_finish)

        main_layout.addWidget(top_bar)

        info_banner = QLabel(
            "<b>Clique 1 e Clique 2</b>: Seleciona os limites da região a ser cortada  |  "
            "<b>Botão Direito</b>: Também inicia/termina corte  |  "
            "<b>Tecla 'd'</b>: Remove o corte sob o cursor  |  "
            "<b>Tecla 'q' ou 'Esc'</b>: Conclui e fecha a janela"
        )
        info_banner.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 10px; color: #334155; font-size: 12px;")
        main_layout.addWidget(info_banner)

        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(4)

        self.fig = Figure(figsize=(10, 7), tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.canvas.mpl_connect('button_press_event', self._on_canvas_click)
        self.canvas.mpl_connect('key_press_event', self._on_key_press)

        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas, 1)
        main_layout.addWidget(plot_container, 1)

        self.lbl_status = QLabel("Click 1st point to start cutting.")
        self.lbl_status.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 500;")
        main_layout.addWidget(self.lbl_status)

    def _clear_cuts(self):
        self.telluric_cuts.clear()
        self.click_pt = None
        self._plot()

    def _on_canvas_click(self, event):
        if event.inaxes != self.ax or event.xdata is None:
            return
        if self.toolbar.mode != '' and event.button != 3:
            return

        clicked_x = float(event.xdata)
        if self.click_pt is None:
            self.click_pt = clicked_x
            self.lbl_status.setText(f"1st Point: {clicked_x:.1f} A. Click 2nd point to cut.")
            self._plot()
        else:
            p1 = float(min(self.click_pt, clicked_x))
            p2 = float(max(self.click_pt, clicked_x))
            if (p2 - p1) > 1.0:
                self.telluric_cuts.append({"low": p1, "upp": p2, "name": "Custom Cut"})
                self.lbl_status.setText(f"Cut region added: {p1:.1f} - {p2:.1f} A")
            self.click_pt = None
            self._plot()

    def _on_key_press(self, event):
        if event.key in ('q',):
            self.accept()
        elif event.key in ('escape',):
            if self.click_pt is not None:
                self.click_pt = None
                self._plot()
                self.lbl_status.setText("Selection canceled.")
            else:
                self.accept()
        elif event.key == 'd' and event.xdata is not None:
            x = float(event.xdata)
            self.telluric_cuts[:] = [c for c in self.telluric_cuts if not (c["low"] <= x <= c["upp"])]
            self._plot()
            self.lbl_status.setText(f"Cut removed at {x:.1f} A.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            self.accept()
        elif event.key() == Qt.Key_Escape:
            if self.click_pt is not None:
                self.click_pt = None
                self._plot()
            else:
                self.accept()
        else:
            super().keyPressEvent(event)

    def _plot(self, preserve_limits=True):
        cur_xlim = self.ax.get_xlim() if preserve_limits and len(self.ax.lines) > 0 else None
        cur_ylim = self.ax.get_ylim() if preserve_limits and len(self.ax.lines) > 0 else None

        self.ax.cla()
        ax = self.ax
        wl, flx, eflx = self.raw_wl, self.raw_flux, self.raw_eflux
        if wl is not None and flx is not None:
            ax.plot(wl, flx, color="#2563EB", lw=1.2, label="Observed Spectrum")
            if eflx is not None and len(eflx) == len(wl):
                ax.fill_between(wl, flx - eflx, flx + eflx, color="#93C5FD", alpha=0.3, label=r"Error ($\pm 1\sigma$)")

            for idx, c in enumerate(self.telluric_cuts):
                lbl = "Cut Region" if idx == 0 else ""
                ax.axvspan(c["low"], c["upp"], color="#EF4444", alpha=0.35, hatch="//", label=lbl)

            if self.click_pt is not None:
                ax.axvline(self.click_pt, color="#DC2626", linestyle="--", lw=2, label=f"1st Point: {self.click_pt:.1f} A")

            ax.legend(loc="upper right", frameon=True)

        ax.set_xlabel(r"Wavelength ($\AA$)", fontsize=12)
        ax.set_ylabel("Flux", fontsize=12)
        ax.set_title("Interactive Spectral Trimming & Telluric Cutting", fontsize=13, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.5)

        if cur_xlim is not None and cur_xlim != (0.0, 1.0) and cur_ylim is not None and cur_ylim != (0.0, 1.0):
            ax.set_xlim(cur_xlim)
            ax.set_ylim(cur_ylim)
        else:
            if wl is not None and len(wl) > 1:
                ax.set_xlim(wl[0], wl[-1])
            self.toolbar.update()

        self.canvas.draw_idle()

