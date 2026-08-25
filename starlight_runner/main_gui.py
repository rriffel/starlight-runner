"""
main_gui.py — Main Graphical User Interface for STARLIGHT Spectral Fitting & Workflow.
Features a 4-step scientific workflow:
  Step 1: Data Preprocessing (Galactic dereddening, restframe shift, rebinning, telluric cut)
  Step 2: Masking & Spectral Regions (Interactive & presets for emission lines/tellurics)
  Step 3: STARLIGHT Grid Setup & Multithread Execution (Config generator, parallel runner)
  Step 4: Output Analysis & Stellar Populations (Synthetic spectrum, residuals, population vectors)
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ReadStarlightParameters import starlightPars, popVectors, StSyntesis
import os
import glob
import traceback
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QCheckBox, QFileDialog,
    QGroupBox, QFormLayout, QSlider, QDoubleSpinBox, QSpinBox,
    QSplitter, QStatusBar, QMessageBox, QProgressBar,
    QStackedWidget, QFrame, QSizePolicy, QScrollArea, QDialog,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QRadioButton
)

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ReadStarlightParameters import starlightPars, popVectors, StSyntesis

if __package__ is None or __package__ == "":
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    __package__ = "starlight_runner"

from .reddening import REDDENING_LAWS, deredden
from .preprocessing import (
    load_spectrum, clean_spectrum, apply_redshift,
    rebin_spectrum, cut_spectral_regions, exclude_spectral_regions,
    trim_spectral_bounds, save_spec_file, DEFAULT_TELLURIC_REGIONS
)
from .masking import SpectralMask, OPTICAL_EMISSION_LINES, NIR_EMISSION_AND_TELLURIC_LINES
from .runner import StarlightConfig, generate_grid_files, run_single_grid
from .parser import StarlightOutput, batch_parse_starlight_outputs
from .custom_widgets import VisualRangeSlider, CollapsibleBox



# Styling constants
ACCENT = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
DARK_BG = "#FFFFFF"
CARD_BG = "#F8FAFC"
TEXT_COLOR = "#0F172A"
MUTED = "#64748B"
BORDER_COLOR = "#CBD5E1"
SUCCESS_COLOR = "#10B981"
DANGER_COLOR = "#EF4444"

STYLESHEET = f"""
QMainWindow {{
    background: {DARK_BG};
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}}

QGroupBox {{
    background: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    margin-top: 18px;
    padding: 16px 12px 12px 12px;
    color: {TEXT_COLOR};
    font-weight: 600;
    font-size: 13px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 2px;
    color: {ACCENT};
    padding: 0 4px;
}}

QLabel {{
    color: {TEXT_COLOR};
    font-size: 13px;
}}

QPushButton {{
    background-color: {ACCENT};
    color: white;
    font-weight: 600;
    font-size: 13px;
    border-radius: 6px;
    padding: 8px 16px;
    border: none;
}}
QPushButton:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton:disabled {{
    background-color: #94A3B8;
    color: #F1F5F9;
}}

QPushButton#navBtn {{
    background-color: transparent;
    color: #64748B;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 600;
    text-align: left;
}}
QPushButton#navBtn:hover {{
    background-color: #F1F5F9;
    color: #1E293B;
}}
QPushButton#navBtn[active="true"] {{
    background-color: #EFF6FF;
    color: {ACCENT};
    border-left: 3px solid {ACCENT};
}}

QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
    background-color: #FFFFFF;
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 6px 10px;
    color: {TEXT_COLOR};
    font-size: 13px;
    min-height: 20px;
}}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 1px solid {ACCENT};
}}

QTableWidget {{
    background-color: #FFFFFF;
    border: 1px solid {BORDER_COLOR};
    gridline-color: #E2E8F0;
    border-radius: 6px;
    color: {TEXT_COLOR};
}}
QHeaderView::section {{
    background-color: #F1F5F9;
    padding: 6px;
    border: 1px solid {BORDER_COLOR};
    font-weight: 600;
    color: #475569;
}}
"""


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



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STARLIGHT Spectral Synthesizer & Workflow Studio")


        self.resize(1350, 900)
        self.setStyleSheet(STYLESHEET)

        # State variables
        self.current_spectrum_path = None
        self.raw_wl = None
        self.raw_flux = None
        self.raw_eflux = None

        self.proc_wl = None
        self.proc_flux = None
        self.proc_eflux = None

        # Interactive telluric cuts & boundary trimming
        self.telluric_cuts = []  # list of {"low": float, "upp": float, "name": str}
        self.preproc_click_pt = None
        self.ax_preproc = None

        # Interactive masking
        self.mask_click_pt = None
        self.ax_mask = None


        self.spectral_mask = SpectralMask()
        self.starlight_config = StarlightConfig()
        self.parsed_output = None
        self.batch_outputs = pd.DataFrame()

        self.worker_thread = None

        # Build UI
        self._init_ui()


    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar navigation
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # Stacked Pages
        self.pages = QStackedWidget(self)
        self.page_preprocess = self._create_step1_preprocess()
        self.page_masking = self._create_step2_masking()
        self.page_runner = self._create_step3_runner()
        self.page_results = self._create_step4_results()

        self.pages.addWidget(self.page_preprocess)
        self.pages.addWidget(self.page_masking)
        self.pages.addWidget(self.page_runner)
        self.pages.addWidget(self.page_results)

        main_layout.addWidget(self.pages, 1)

        # Status Bar
        self.statusBar().showMessage("Ready — Select or load a spectrum to begin.")
        self.set_active_page(0)

    def _create_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background-color: {CARD_BG}; border-right: 1px solid {BORDER_COLOR};")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(8)

        # App Title
        title_label = QLabel("STARLIGHT")
        title_label.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {ACCENT}; margin-bottom: 2px;")
        sub_label = QLabel("Runner & Analyser v1.0")
        sub_label.setStyleSheet(f"font-size: 11px; color: {MUTED}; margin-bottom: 16px;")
        layout.addWidget(title_label)
        layout.addWidget(sub_label)

        # Step Navigation Buttons
        self.nav_buttons = []
        steps = [
            ("1. Data Preprocessing", 0),
            ("2. Spectral Masking", 1),
            ("3. STARLIGHT Grid", 2),
            ("4. Results & Analysis", 3)
        ]

        for text, idx in steps:
            btn = QPushButton(text)
            btn.setObjectName("navBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx: self.set_active_page(i))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addSpacing(20)

        # Global Config Buttons (Moved up so they don't get clipped on small screens)
        lbl_cfg = QLabel("Global Configuration")
        lbl_cfg.setStyleSheet(f"color: {ACCENT}; font-size: 11px; font-weight: bold; margin-bottom: 2px;")
        layout.addWidget(lbl_cfg)
        
        btn_load_cfg = QPushButton("Load Config State")
        btn_load_cfg.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px; color: #334155;")
        btn_load_cfg.setCursor(Qt.PointingHandCursor)
        btn_load_cfg.clicked.connect(self._on_load_config_state)
        layout.addWidget(btn_load_cfg)
        
        btn_save_cfg = QPushButton("Save Config State")
        btn_save_cfg.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px; color: #334155;")
        btn_save_cfg.setCursor(Qt.PointingHandCursor)
        btn_save_cfg.clicked.connect(self._on_save_config_state)
        layout.addWidget(btn_save_cfg)

        layout.addStretch()

        # Footer info
        footer = QLabel("Rogério Riffel\nUFRGS / Depto Astronomia")
        footer.setStyleSheet(f"color: {MUTED}; font-size: 11px; line-height: 1.4;")
        layout.addWidget(footer)

        return sidebar

    def set_active_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if index == 1:
            # Sync Step 2 (Masking)
            if hasattr(self, 'lbl_mask_loaded_file'):
                if self.current_spectrum_path:
                    self.lbl_mask_loaded_file.setText(os.path.basename(self.current_spectrum_path))
                elif self.proc_wl is not None or self.raw_wl is not None:
                    self.lbl_mask_loaded_file.setText("Espectro ativo na memória")
            self._plot_masking()
        elif index == 2:
            # Sync Step 3 (Runner) observation directory if available
            if hasattr(self, 'txt_obs_dir') and self.current_spectrum_path:
                obs_d = os.path.dirname(os.path.abspath(self.current_spectrum_path))
                if obs_d and os.path.exists(obs_d):
                    self.txt_obs_dir.setText(obs_d)
                    self.starlight_config.obs_dir = obs_d
        elif index == 3:
            # Sync Step 4 (Results)
            if hasattr(self, '_plot_results') and self.parsed_output is not None:
                self._plot_results()


    # -------------------------------------------------------------
    # STEP 1: PREPROCESSING PAGE
    # -------------------------------------------------------------
    def _create_step1_preprocess(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left control panel inside scroll area for comfort
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedWidth(420)
        scroll_area.setFrameShape(QFrame.NoFrame)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(12)

        # 1. File Load Group
        grp_load = QGroupBox("1. Load Spectrum")
        f_load = QVBoxLayout(grp_load)
        btn_open = QPushButton("Carregar Espectro (.txt, .spec, .fits)")
        btn_open.clicked.connect(self._on_load_spectrum_dialog)
        self.lbl_loaded_file = QLabel("No file loaded")
        self.lbl_loaded_file.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        f_load.addWidget(btn_open)
        f_load.addWidget(self.lbl_loaded_file)
        left_layout.addWidget(grp_load)

        # 2. Physical Corrections Group
        grp_corr = QGroupBox("2. Physical Corrections")
        form_corr = QFormLayout(grp_corr)
        form_corr.setSpacing(10)

        self.spin_z = QDoubleSpinBox()
        self.spin_z.setRange(0.0, 10.0)
        self.spin_z.setDecimals(6)
        self.spin_z.setSingleStep(0.001)
        self.spin_z.setValue(0.0)
        form_corr.addRow("Redshift (z):", self.spin_z)

        self.combo_law = QComboBox()
        for k in REDDENING_LAWS.keys():
            self.combo_law.addItem(k)
        form_corr.addRow("Extinction Law:", self.combo_law)

        self.spin_av = QDoubleSpinBox()
        self.spin_av.setRange(0.0, 20.0)
        self.spin_av.setDecimals(4)
        self.spin_av.setSingleStep(0.05)
        self.spin_av.setValue(0.0)
        form_corr.addRow("Extinction A_V (mag):", self.spin_av)

        self.spin_rv = QDoubleSpinBox()
        self.spin_rv.setRange(1.0, 10.0)
        self.spin_rv.setDecimals(2)
        self.spin_rv.setValue(3.1)
        form_corr.addRow("R_V:", self.spin_rv)

        left_layout.addWidget(grp_corr)

        # 3. Rebinning Group
        grp_rebin = QGroupBox("3. Rebinning")
        form_rebin = QFormLayout(grp_rebin)
        form_rebin.setSpacing(10)

        self.spin_rebin_step = QDoubleSpinBox()
        self.spin_rebin_step.setRange(0.1, 100.0)
        self.spin_rebin_step.setDecimals(2)
        self.spin_rebin_step.setValue(1.0)
        self.spin_rebin_step.setSuffix(" Å")
        form_rebin.addRow("Step (Δλ):", self.spin_rebin_step)
        left_layout.addWidget(grp_rebin)

        # 4. Interactive Telluric & Boundary Cutting
        grp_cut = QGroupBox("4. Telluric & Extremity Cuts (Interativo)")
        f_cut = QVBoxLayout(grp_cut)
        f_cut.setSpacing(10)

        # Interactive Mode Toggle Button
        self.btn_interactive_cut = QPushButton("Modo Interativo: Cortar no Gráfico")
        self.btn_interactive_cut.setCheckable(True)
        self.btn_interactive_cut.setStyleSheet("""
            QPushButton:checked {
                background-color: #10B981;
                color: white;
                font-weight: bold;
                border: 2px solid #059669;
            }
        """)
        self.btn_interactive_cut.clicked.connect(self._on_toggle_interactive_cut)
        f_cut.addWidget(self.btn_interactive_cut)

        btn_detach_cut = QPushButton("Janela Externa de Corte (Tela Cheia)")
        btn_detach_cut.setStyleSheet("background-color: #4F46E5; color: white; font-weight: bold; padding: 7px; font-size: 12px;")
        btn_detach_cut.clicked.connect(self._on_open_detached_cut_dialog)
        f_cut.addWidget(btn_detach_cut)

        self.lbl_cut_mode_help = QLabel("Dica: Clique no 1º e 2º ponto sobre o espectro para cortar regiões ou extremidades.")
        self.lbl_cut_mode_help.setWordWrap(True)
        self.lbl_cut_mode_help.setStyleSheet("color: #64748B; font-size: 11px; font-style: italic;")
        f_cut.addWidget(self.lbl_cut_mode_help)

        # Preset & Clear buttons row
        btn_row = QHBoxLayout()
        btn_nir_tel_preset = QPushButton("Preset Telúricas NIR")
        btn_nir_tel_preset.clicked.connect(self._apply_nir_telluric_preset)
        btn_clear_cuts = QPushButton("Clear Cuts")
        btn_clear_cuts.setStyleSheet("background-color: #EF4444; color: white;")
        btn_clear_cuts.clicked.connect(self._clear_all_cuts)
        btn_row.addWidget(btn_nir_tel_preset)
        btn_row.addWidget(btn_clear_cuts)
        f_cut.addLayout(btn_row)

        # Manual Interval Addition
        manual_row = QHBoxLayout()
        self.spin_cut_low = QDoubleSpinBox()
        self.spin_cut_low.setRange(0.0, 100000.0)
        self.spin_cut_low.setDecimals(1)
        self.spin_cut_low.setValue(13400.0)
        self.spin_cut_upp = QDoubleSpinBox()
        self.spin_cut_upp.setRange(0.0, 100000.0)
        self.spin_cut_upp.setDecimals(1)
        self.spin_cut_upp.setValue(14200.0)
        btn_add_cut = QPushButton("+ Adicionar")
        btn_add_cut.clicked.connect(self._add_manual_cut)
        manual_row.addWidget(QLabel("λ:"))
        manual_row.addWidget(self.spin_cut_low)
        manual_row.addWidget(QLabel("-"))
        manual_row.addWidget(self.spin_cut_upp)
        manual_row.addWidget(btn_add_cut)
        f_cut.addLayout(manual_row)

        # Cuts Table
        self.tbl_cuts = QTableWidget(0, 2)
        self.tbl_cuts.setHorizontalHeaderLabels(["Início (Å)", "Fim (Å)"])
        self.tbl_cuts.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_cuts.setMinimumHeight(120)
        f_cut.addWidget(self.tbl_cuts)

        btn_del_cut = QPushButton("Remover Corte Selecionado")
        btn_del_cut.clicked.connect(self._remove_selected_cut)
        f_cut.addWidget(btn_del_cut)

        # Global Boundary Trimming
        self.chk_trim_bounds = QCheckBox("Cortar Extremos Globais do Espectro")
        self.chk_trim_bounds.toggled.connect(self._plot_preprocessing)
        f_cut.addWidget(self.chk_trim_bounds)

        bounds_row = QHBoxLayout()
        self.spin_trim_min = QDoubleSpinBox()
        self.spin_trim_min.setRange(0.0, 100000.0)
        self.spin_trim_min.setDecimals(1)
        self.spin_trim_max = QDoubleSpinBox()
        self.spin_trim_max.setRange(0.0, 100000.0)
        self.spin_trim_max.setDecimals(1)
        bounds_row.addWidget(QLabel("λ min:"))
        bounds_row.addWidget(self.spin_trim_min)
        bounds_row.addWidget(QLabel("λ max:"))
        bounds_row.addWidget(self.spin_trim_max)
        f_cut.addLayout(bounds_row)

        left_layout.addWidget(grp_cut)

        # Action Buttons
        btn_apply_preprocess = QPushButton("Executar Pré-processamento")
        btn_apply_preprocess.setStyleSheet("background-color: #2563EB; color: white; font-size: 14px; padding: 10px;")
        btn_apply_preprocess.clicked.connect(self._on_run_preprocessing)
        left_layout.addWidget(btn_apply_preprocess)

        btn_export_spec = QPushButton("Salvar Espectro (.spec)")
        btn_export_spec.clicked.connect(self._on_export_spec_dialog)
        left_layout.addWidget(btn_export_spec)

        btn_next_step2 = QPushButton("Avançar para Etapa 2 (Spectral Masking)  ➔")
        btn_next_step2.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 9px; font-size: 13px;")
        btn_next_step2.clicked.connect(lambda: self.set_active_page(1))
        left_layout.addWidget(btn_next_step2)


        left_layout.addStretch()

        scroll_area.setWidget(left_panel)
        scroll_area.setMinimumWidth(380)
        scroll_area.setMaximumWidth(520)

        # Right plot area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.fig_preproc = Figure(figsize=(8, 6), tight_layout=True)
        self.canvas_preproc = FigureCanvas(self.fig_preproc)
        self.ax_preproc = self.fig_preproc.add_subplot(111)
        self.toolbar_preproc = NavigationToolbar(self.canvas_preproc, self)

        # Connect canvas events for interactive extremity and telluric cutting
        self.canvas_preproc.mpl_connect('button_press_event', self._on_preproc_canvas_click)
        self.canvas_preproc.mpl_connect('key_press_event', self._on_preproc_key_press)

        right_layout.addWidget(self.toolbar_preproc)
        right_layout.addWidget(self.canvas_preproc)

        # Resizable Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(scroll_area)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        return page



    def _on_toggle_interactive_cut(self, checked):
        self.preproc_click_pt = None
        if checked:
            # Turn off zoom/pan tool if active so clicks go to cutting tool
            if self.toolbar_preproc.mode != '':
                self.toolbar_preproc.zoom()  # toggles off
            self.btn_interactive_cut.setText("🟢 Modo Interativo Ativo (Clique no Gráfico)")
            self.statusBar().showMessage("Modo Interativo ATIVADO: Clique no 1º e no 2º extremo da região para cortar (ou use botão direito).")
        else:
            self.btn_interactive_cut.setText("✂️ Modo Interativo: Cortar no Gráfico")
            self.statusBar().showMessage("Modo Interativo Desativado.")
        self._plot_preprocessing()

    def _on_preproc_canvas_click(self, event):
        # Allow if interactive button is checked OR if user uses Right Click (button 3)
        is_interactive = self.btn_interactive_cut.isChecked()
        is_right_click = (event.button == 3)
        is_left_click = (event.button == 1)

        if not (is_interactive or is_right_click):
            return

        if event.inaxes is None or event.xdata is None:
            return

        # If toolbar is actively in zoom or pan mode and user clicked left, don't interrupt
        if self.toolbar_preproc.mode != '' and not is_right_click:
            return

        clicked_x = float(event.xdata)

        if self.preproc_click_pt is None:
            # 1st Click: record starting extremity
            self.preproc_click_pt = clicked_x
            self.statusBar().showMessage(
                f"📍 1º Extremo selecionado em {clicked_x:.1f} Å. Clique no 2º extremo para completar o corte (ou 'Esc' para cancelar)."
            )
            self._plot_preprocessing()
        else:
            # 2nd Click: record ending extremity and create cut interval
            p1 = float(min(self.preproc_click_pt, clicked_x))
            p2 = float(max(self.preproc_click_pt, clicked_x))
            
            if (p2 - p1) > 1.0:
                self.telluric_cuts.append({"low": p1, "upp": p2, "name": "Telluric cut"})
                self.statusBar().showMessage(
                    f"✅ Corte adicionado: {p1:.1f} - {p2:.1f} Å. Clique novamente para iniciar outro corte."
                )
            else:
                self.statusBar().showMessage("⚠️ Intervalo muito pequeno (menor que 1 Å). Cancelado.")

            self.preproc_click_pt = None
            self._update_cuts_table()
            self._plot_preprocessing()

    def _on_preproc_key_press(self, event):
        if event.key == 'escape':
            self.preproc_click_pt = None
            self._plot_preprocessing()
            self.statusBar().showMessage("Seleção de corte cancelada.")
        elif event.key == 'd' and event.xdata is not None:
            # Delete any cut region under mouse
            x = float(event.xdata)
            to_remove = [i for i, c in enumerate(self.telluric_cuts) if c["low"] <= x <= c["upp"]]
            if to_remove:
                for idx in reversed(to_remove):
                    del self.telluric_cuts[idx]
                self._update_cuts_table()
                self._plot_preprocessing()
                self.statusBar().showMessage(f"🗑️ Cut removed at {x:.1f} Å.")


    def _apply_nir_telluric_preset(self):
        # Standard NIR telluric absorption bands
        nir_bands = [
            (13400.0, 14200.0),
            (18000.0, 19000.0)
        ]
        for low, upp in nir_bands:
            if not any(abs(c["low"] - low) < 50 and abs(c["upp"] - upp) < 50 for c in self.telluric_cuts):
                self.telluric_cuts.append({"low": low, "upp": upp, "name": "NIR Telluric gap"})
        self._update_cuts_table()
        self._plot_preprocessing()
        self.statusBar().showMessage("Presets de bandas telúricas NIR carregados.")

    def _clear_all_cuts(self):
        self.telluric_cuts.clear()
        self.preproc_click_pt = None
        self._update_cuts_table()
        self._plot_preprocessing()
        self.statusBar().showMessage("Todos os cortes foram removidos.")

    def _add_manual_cut(self):
        low = self.spin_cut_low.value()
        upp = self.spin_cut_upp.value()
        if low >= upp:
            QMessageBox.warning(self, "Intervalo Inválido", "O início deve ser menor que o fim.")
            return
        self.telluric_cuts.append({"low": low, "upp": upp, "name": "Telluric cut"})
        self._update_cuts_table()
        self._plot_preprocessing()

    def _remove_selected_cut(self):
        row = self.tbl_cuts.currentRow()
        if 0 <= row < len(self.telluric_cuts):
            self.telluric_cuts.pop(row)
            self._update_cuts_table()
            self._plot_preprocessing()

    def _update_cuts_table(self):
        self.telluric_cuts.sort(key=lambda x: x["low"])
        self.tbl_cuts.setRowCount(len(self.telluric_cuts))
        for r, it in enumerate(self.telluric_cuts):
            self.tbl_cuts.setItem(r, 0, QTableWidgetItem(f"{it['low']:.1f}"))
            self.tbl_cuts.setItem(r, 1, QTableWidgetItem(f"{it['upp']:.1f}"))

    def _on_load_spectrum_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Spectrum File", "", "Spectra (*.txt *.dat *.csv *.spec *.fits);;All Files (*)"
        )
        if filepath:
            self.load_spectrum_file(filepath)

    def load_spectrum_file(self, filepath):
        try:
            wl, flx, eflx = load_spectrum(filepath)
            wl_c, flx_c, eflx_c = clean_spectrum(wl, flx, eflx)
            self.raw_wl, self.raw_flux, self.raw_eflux = wl_c, flx_c, eflx_c
            self.current_spectrum_path = filepath
            self.lbl_loaded_file.setText(os.path.basename(filepath))

            # Set default trim bounds
            if len(wl_c) > 0:
                self.spin_trim_min.setValue(wl_c[0])
                self.spin_trim_max.setValue(wl_c[-1])

            self.statusBar().showMessage(f"Loaded: {os.path.basename(filepath)} ({len(wl_c)} points)")
            self._plot_preprocessing()
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Spectrum", str(e))

    def _on_run_preprocessing(self):
        if self.raw_wl is None:
            QMessageBox.warning(self, "No Spectrum Loaded", "Please load a spectrum first.")
            return

        try:
            z = self.spin_z.value()
            av = self.spin_av.value()
            rv = self.spin_rv.value()
            law = self.combo_law.currentText()
            step = self.spin_rebin_step.value()

            # 1. Deredden
            wl_d, flx_d, eflx_d = deredden(
                self.raw_wl, self.raw_flux, eflux=self.raw_eflux,
                law=law, av=av, rv=rv
            )

            # 2. Shift to rest frame
            wl_curr = apply_redshift(wl_d, z)
            flx_curr = flx_d
            eflx_curr = eflx_d

            # 3. Global boundary trimming if enabled
            if self.chk_trim_bounds.isChecked():
                w_min = self.spin_trim_min.value()
                w_max = self.spin_trim_max.value()
                if w_min < w_max:
                    wl_curr, flx_curr, eflx_curr = trim_spectral_bounds(
                        wl_curr, flx_curr, eflux=eflx_curr, wl_min=w_min, wl_max=w_max
                    )

            if len(wl_curr) < 3:
                raise ValueError("Restaram poucos pontos válidos após aplicar os cortes. Revise os limites.")

            # 4. Rebinning
            wl_reb, flx_reb, eflx_reb = rebin_spectrum(
                wl_curr, flx_curr, eflux=eflx_curr, step=step
            )

            # 5. Exclude telluric / interactive cut regions
            if self.telluric_cuts:
                cut_intervals = [(c["low"], c["upp"]) for c in self.telluric_cuts]
                wl_reb, flx_reb, eflx_reb = exclude_spectral_regions(
                    wl_reb, flx_reb, eflux=eflx_reb, regions=cut_intervals
                )

            self.proc_wl, self.proc_flux, self.proc_eflux = wl_reb, flx_reb, eflx_reb
            self._plot_preprocessing()
            self.statusBar().showMessage(f"Pré-processamento concluído com sucesso ({len(wl_reb)} pontos).")
        except Exception as e:
            QMessageBox.critical(self, "Preprocessing Error", str(e))

    def _plot_preprocessing(self, preserve_limits=True):
        cur_xlim = self.ax_preproc.get_xlim() if preserve_limits and len(self.ax_preproc.lines) > 0 else None
        cur_ylim = self.ax_preproc.get_ylim() if preserve_limits and len(self.ax_preproc.lines) > 0 else None

        self.ax_preproc.cla()
        ax = self.ax_preproc

        if self.raw_wl is not None:
            ax.plot(self.raw_wl, self.raw_flux, color="#94A3B8", lw=1.0, alpha=0.7, label="Raw Observed")

        if self.proc_wl is not None:
            ax.plot(self.proc_wl, self.proc_flux, color="#2563EB", lw=1.5, label="Corrected & Rebinned")
            if self.proc_eflux is not None:
                ax.fill_between(
                    self.proc_wl,
                    self.proc_flux - self.proc_eflux,
                    self.proc_flux + self.proc_eflux,
                    color="#93C5FD", alpha=0.35, label=r"Error ($\pm 1\sigma$)"
                )

        # Highlight Telluric / Cut Regions in Red with Hatching
        for idx, cut in enumerate(self.telluric_cuts):
            lbl = "Cut Region (Telurica)" if idx == 0 else ""
            ax.axvspan(cut["low"], cut["upp"], color="#EF4444", alpha=0.32, hatch="//", label=lbl)

        # Highlight single click guide if user clicked 1st point
        if self.preproc_click_pt is not None:
            ax.axvline(self.preproc_click_pt, color="#DC2626", linestyle="--", lw=2, label=f"1st Point: {self.preproc_click_pt:.1f} A")

        # Global Trim Bounds preview if enabled
        if self.chk_trim_bounds.isChecked():
            t_min = self.spin_trim_min.value()
            t_max = self.spin_trim_max.value()
            if t_min > 0: ax.axvline(t_min, color="#059669", linestyle=":", lw=1.5, label=r"Global Limit $\lambda_{\min}$")
            if t_max > 0: ax.axvline(t_max, color="#059669", linestyle=":", lw=1.5, label=r"Global Limit $\lambda_{\max}$")

        ax.set_xlabel(r"Wavelength ($\AA$)", fontsize=12)
        ax.set_ylabel("Flux (arbitrary / calibrated units)", fontsize=12)
        ax.set_title("Spectral Preprocessing & Telluric Cutting", fontsize=13, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper right", frameon=True)

        if cur_xlim is not None and cur_xlim != (0.0, 1.0) and cur_ylim is not None and cur_ylim != (0.0, 1.0):
            ax.set_xlim(cur_xlim)
            ax.set_ylim(cur_ylim)
        else:
            w = self.proc_wl if self.proc_wl is not None else self.raw_wl
            if w is not None and len(w) > 1:
                ax.set_xlim(w[0], w[-1])
            self.toolbar_preproc.update()

        self.canvas_preproc.draw_idle()



    def _on_export_spec_dialog(self):
        wl = self.proc_wl if self.proc_wl is not None else self.raw_wl
        flx = self.proc_flux if self.proc_flux is not None else self.raw_flux
        eflx = self.proc_eflux if self.proc_eflux is not None else self.raw_eflux

        if wl is None or flx is None:
            QMessageBox.warning(self, "No Data", "No spectrum data to export.")
            return

        default_name = "spectrum_clean.spec"
        if self.current_spectrum_path:
            base = os.path.splitext(os.path.basename(self.current_spectrum_path))[0]
            default_name = f"{base}_clean.spec"

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Starlight .spec File", default_name, "STARLIGHT Spec (*.spec);;All Files (*)"
        )
        if out_path:
            save_spec_file(out_path, wl, flx, eflx)
            self.current_spectrum_path = out_path
            if hasattr(self, 'lbl_mask_loaded_file'):
                self.lbl_mask_loaded_file.setText(f"{os.path.basename(out_path)} ({len(wl)} pts)")

            reply = QMessageBox.question(
                self,
                "Espectro Salvo",
                f"Espectro salvo com sucesso em:\n{out_path}\n\nDeseja avançar para a Etapa ② (Spectral Masking) com este espectro?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.set_active_page(1)
            else:
                self.statusBar().showMessage(f"Salvo: {out_path}")

    def _on_open_detached_cut_dialog(self):
        wl = self.raw_wl
        flx = self.raw_flux
        eflx = self.raw_eflux

        if wl is None or flx is None:
            QMessageBox.warning(self, "Sem Espectro", "Por favor, carregue um espectro primeiro na Etapa 1.")
            return

        dlg = InteractiveCutDialog(self, wl, flx, eflx, self.telluric_cuts)
        if dlg.exec_() == QDialog.Accepted:
            self.telluric_cuts = dlg.telluric_cuts
            self._update_cuts_table()
            self._plot_preprocessing()
            self.statusBar().showMessage(f"Cortes atualizados ({len(self.telluric_cuts)} regiões cortadas).")

    def _on_open_detached_mask_dialog(self):
        wl = self.proc_wl if self.proc_wl is not None else self.raw_wl
        flx = self.proc_flux if self.proc_flux is not None else self.raw_flux
        eflx = self.proc_eflux if self.proc_eflux is not None else self.raw_eflux

        if wl is None or flx is None:
            QMessageBox.warning(self, "Sem Espectro", "Por favor, carregue ou pré-processe um espectro primeiro.")
            return

        spec_path = getattr(self, 'current_spectrum_path', None)
        mask_dir = self.txt_mask_dir_step2.text().strip() if hasattr(self, 'txt_mask_dir_step2') else None
        dlg = InteractiveMaskDialog(self, wl, flx, eflx, self.spectral_mask, spectrum_path=spec_path, mask_dir=mask_dir)
        if dlg.exec_() == QDialog.Accepted:
            self.spectral_mask = dlg.spectral_mask
            self._update_mask_table()
            self._plot_masking()

            # Automatically persist mask
            if spec_path and len(self.spectral_mask.intervals) > 0:
                mask_ext = self.starlight_config.mask_ext or ".mask"
                if not mask_ext.startswith('.'): mask_ext = "." + mask_ext
                spec_base = os.path.splitext(os.path.basename(spec_path))[0]
                
                # Fetch mask_dir from the dialog just in case the user edited it
                final_mask_dir = dlg.txt_dlg_mask_dir.text().strip() if hasattr(dlg, 'txt_dlg_mask_dir') else mask_dir
                
                if final_mask_dir:
                    os.makedirs(final_mask_dir, exist_ok=True)
                    auto_mask = os.path.join(final_mask_dir, f"{spec_base}{mask_ext}")
                    # Update main window field
                    if hasattr(self, 'txt_mask_dir_step2'):
                        self.txt_mask_dir_step2.setText(final_mask_dir)
                else:
                    spec_dir = os.path.dirname(spec_path)
                    auto_mask = os.path.join(spec_dir, f"{spec_base}{mask_ext}") if spec_dir else f"{spec_base}{mask_ext}"

                try:
                    self.spectral_mask.save_to_file(auto_mask)
                    self.statusBar().showMessage(f"✅ Auto-saved mask: {auto_mask} ({len(self.spectral_mask.intervals)} intervals)")
                except Exception as e:
                    self.statusBar().showMessage(f"Masking done ({len(self.spectral_mask.intervals)} intervals).")
            else:
                self.statusBar().showMessage(f"Edição de máscaras concluída ({len(self.spectral_mask.intervals)} intervalos).")




    # -------------------------------------------------------------
    # STEP 2: MASKING PAGE

    # -------------------------------------------------------------
    def _create_step2_masking(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left control panel
        left_panel = QWidget()
        left_panel.setFixedWidth(420)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # 0. Target Spectrum Group
        grp_spec = QGroupBox("0. Target Spectrum")
        f_spec = QVBoxLayout(grp_spec)
        btn_load_spec_mask = QPushButton("Carregar Espectro (.spec, .txt, .fits)")
        btn_load_spec_mask.clicked.connect(self._on_load_spectrum_for_masking_dialog)
        self.lbl_mask_loaded_file = QLabel("No spectrum loaded (or use from Step 1)")
        self.lbl_mask_loaded_file.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        f_spec.addWidget(btn_load_spec_mask)
        f_spec.addWidget(self.lbl_mask_loaded_file)
        left_layout.addWidget(grp_spec)

        # 1. Masks Directory
        grp_mdir = QGroupBox("1. Masks Directory")
        f_mdir = QHBoxLayout(grp_mdir)
        self.txt_mask_dir_step2 = QLineEdit(self.starlight_config.mask_dir)
        self.txt_mask_dir_step2.setPlaceholderText("e.g. masks/")
        self.txt_mask_dir_step2.textChanged.connect(self._sync_mask_dirs)
        btn_browse_mdir2 = QPushButton("...")
        btn_browse_mdir2.setFixedWidth(36)
        btn_browse_mdir2.clicked.connect(self._on_browse_mask_dir_step2)
        f_mdir.addWidget(self.txt_mask_dir_step2)
        f_mdir.addWidget(btn_browse_mdir2)
        left_layout.addWidget(grp_mdir)

        # 1. Interactive Masking (CreateMasks Mode)
        grp_interactive = QGroupBox("2. Modo Interativo (CreateMasks)")
        f_inter = QVBoxLayout(grp_interactive)
        f_inter.setSpacing(8)

        self.btn_mask_interactive = QPushButton("Modo Interativo: Mascarar no Gráfico")
        self.btn_mask_interactive.setCheckable(True)
        self.btn_mask_interactive.setStyleSheet("""
            QPushButton:checked {
                background-color: #10B981;
                color: white;
                font-weight: bold;
                border: 2px solid #059669;
            }
        """)
        self.btn_mask_interactive.clicked.connect(self._on_toggle_mask_interactive)
        f_inter.addWidget(self.btn_mask_interactive)

        btn_detach_mask = QPushButton("Janela Externa de Máscara (CreateMasks)")
        btn_detach_mask.setStyleSheet("background-color: #4F46E5; color: white; font-weight: bold; padding: 8px; font-size: 13px;")
        btn_detach_mask.clicked.connect(self._on_open_detached_mask_dialog)
        f_inter.addWidget(btn_detach_mask)

        # Weight selection for Left-Click
        weight_row = QHBoxLayout()
        weight_row.addWidget(QLabel("Peso do Clique:"))
        self.rb_weight_0 = QRadioButton("🔴 Peso 0.0 (Exclude)")
        self.rb_weight_0.setChecked(True)
        self.rb_weight_2 = QRadioButton("🟢 Peso 2.0 (Emphasize)")
        weight_row.addWidget(self.rb_weight_0)
        weight_row.addWidget(self.rb_weight_2)
        f_inter.addLayout(weight_row)

        lbl_mask_help = QLabel(
            "<b>Botão Direito (Right-Click)</b>: 1º e 2º clique marca Peso 0.0 (Vermelho)<br>"
            "<b>Botão do Meio (Middle-Click)</b>: 1º e 2º clique marca Peso 2.0 (Verde)<br>"
            "<b>Botão Esquerdo</b>: Zoom/Pan (ou Máscara quando Modo Interativo estiver ativo)<br>"
            "<b>Tecla 'd'</b>: Remova uma máscara passando o mouse sobre ela e teclando 'd'<br>"
            "<b>Tecla 'Esc'</b>: Cancela a seleção do 1º ponto"
        )
        lbl_mask_help.setWordWrap(True)
        lbl_mask_help.setStyleSheet("color: #475569; font-size: 11px; line-height: 1.3; background: #F1F5F9; padding: 6px; border-radius: 4px;")
        f_inter.addWidget(lbl_mask_help)
        left_layout.addWidget(grp_interactive)

        # 2. Presets Group
        grp_presets = QGroupBox("3. Mask Presets")
        f_pre = QVBoxLayout(grp_presets)

        btn_opt_preset = QPushButton("Carregar Preset Óptico (CreateMasks)")
        btn_opt_preset.clicked.connect(lambda: self._apply_mask_preset("optical"))
        f_pre.addWidget(btn_opt_preset)

        btn_nir_preset = QPushButton("Carregar Preset NIR")
        btn_nir_preset.clicked.connect(lambda: self._apply_mask_preset("nir"))
        f_pre.addWidget(btn_nir_preset)

        btn_clear_masks = QPushButton("Limpar Todas as Máscaras")
        btn_clear_masks.setStyleSheet("background-color: #EF4444; color: white;")
        btn_clear_masks.clicked.connect(self._clear_all_masks)
        f_pre.addWidget(btn_clear_masks)

        left_layout.addWidget(grp_presets)

        # 3. Manual Interval Group
        grp_add = QGroupBox("4. Add Mask Region Manualmente")
        f_add = QFormLayout(grp_add)
        self.spin_mask_low = QDoubleSpinBox()
        self.spin_mask_low.setRange(0.0, 50000.0)
        self.spin_mask_low.setValue(6540.0)
        f_add.addRow("Low λ (Å):", self.spin_mask_low)

        self.spin_mask_upp = QDoubleSpinBox()
        self.spin_mask_upp.setRange(0.0, 50000.0)
        self.spin_mask_upp.setValue(6600.0)
        f_add.addRow("Upper λ (Å):", self.spin_mask_upp)

        self.spin_mask_weight = QDoubleSpinBox()
        self.spin_mask_weight.setRange(0.0, 100.0)
        self.spin_mask_weight.setValue(0.0)
        f_add.addRow("Weight (0=mask, 2=key):", self.spin_mask_weight)

        self.txt_mask_name = QLineEdit()
        self.txt_mask_name.setPlaceholderText("e.g. Halpha emission")
        f_add.addRow("Label:", self.txt_mask_name)

        btn_add_interval = QPushButton("+ Adicionar Região")
        btn_add_interval.clicked.connect(self._on_add_mask_interval)
        f_add.addRow(btn_add_interval)
        left_layout.addWidget(grp_add)

        # 4. Mask Table
        self.tbl_masks = QTableWidget(0, 4)
        self.tbl_masks.setHorizontalHeaderLabels(["Low (Å)", "Upp (Å)", "Weight", "Label"])
        self.tbl_masks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_masks.setMinimumHeight(130)
        left_layout.addWidget(self.tbl_masks, 1)

        btn_del_mask = QPushButton("Remover Região Selecionada")
        btn_del_mask.clicked.connect(self._remove_selected_mask)
        left_layout.addWidget(btn_del_mask)

        # I/O Buttons
        io_row = QHBoxLayout()
        btn_load_sm = QPushButton("Abrir Máscara (.mask)")
        btn_load_sm.clicked.connect(self._on_open_sm_dialog)
        btn_save_sm = QPushButton("Salvar Máscara (.mask)")
        btn_save_sm.clicked.connect(self._on_save_sm_dialog)
        io_row.addWidget(btn_load_sm)
        io_row.addWidget(btn_save_sm)
        left_layout.addLayout(io_row)

        btn_next_step3 = QPushButton("Avançar para Etapa 3 (STARLIGHT Grid)  ➔")
        btn_next_step3.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 9px; font-size: 13px;")
        btn_next_step3.clicked.connect(lambda: self.set_active_page(2))
        left_layout.addWidget(btn_next_step3)


        left_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(380)
        scroll_area.setMaximumWidth(520)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(left_panel)

        # Right plot area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.fig_mask = Figure(figsize=(8, 6), tight_layout=True)
        self.canvas_mask = FigureCanvas(self.fig_mask)
        self.ax_mask = self.fig_mask.add_subplot(111)
        self.toolbar_mask = NavigationToolbar(self.canvas_mask, self)

        # Connect canvas events for interactive masking
        self.canvas_mask.mpl_connect('button_press_event', self._on_mask_canvas_click)
        self.canvas_mask.mpl_connect('key_press_event', self._on_mask_key_press)

        right_layout.addWidget(self.toolbar_mask)
        right_layout.addWidget(self.canvas_mask)

        # Dynamic Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(scroll_area)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        return page


    def _on_toggle_mask_interactive(self, checked):
        self.mask_click_pt = None
        if checked:
            if self.toolbar_mask.mode != '':
                self.toolbar_mask.zoom()  # toggle off zoom mode
            self.btn_mask_interactive.setText("🟢 Modo Interativo de Máscara ATIVO")
            self.statusBar().showMessage("Modo Interativo de Máscara Ativo: Clique no 1º e 2º ponto sobre o espectro para mascarar.")
        else:
            self.btn_mask_interactive.setText("✂️ Modo Interativo: Mascarar no Gráfico")
            self.statusBar().showMessage("Modo Interativo de Máscara Desativado.")
        self._plot_masking()

    def _on_mask_canvas_click(self, event):
        if self.ax_mask is None or event.inaxes != self.ax_mask or event.xdata is None:
            return

        is_interactive = self.btn_mask_interactive.isChecked()
        is_right = (event.button == 3)
        is_middle = (event.button == 2)
        is_left = (event.button == 1)

        # Don't intercept left click if interactive mode is off (allow zoom/pan toolbar)
        if not (is_interactive or is_right or is_middle):
            return
        if self.toolbar_mask.mode != '' and not (is_right or is_middle):
            return

        clicked_x = float(event.xdata)

        # Determine weight
        if is_right:
            weight = 0.0
        elif is_middle:
            weight = 2.0
        else:
            weight = 0.0 if self.rb_weight_0.isChecked() else 2.0

        if self.mask_click_pt is None:
            self.mask_click_pt = clicked_x
            self.mask_click_weight = weight
            w_txt = "0.0 (Exclude)" if weight == 0.0 else "2.0 (Emphasize)"
            self.statusBar().showMessage(f"📍 1º ponto em {clicked_x:.1f} Å. Clique no 2º ponto para aplicar máscara com peso {w_txt} (ou 'Esc' para cancelar).")
            self._plot_masking()
        else:
            p1 = float(min(self.mask_click_pt, clicked_x))
            p2 = float(max(self.mask_click_pt, clicked_x))
            w = self.mask_click_weight if hasattr(self, 'mask_click_weight') else weight

            if (p2 - p1) > 1.0:
                name = "Mask (Weight 0)" if w == 0.0 else "Key Feature (Weight 2)"
                self.spectral_mask.add_interval(p1, p2, weight=w, name=name)
                self.statusBar().showMessage(f"✅ Região mascarada adicionada: {p1:.1f} - {p2:.1f} Å (peso={w:.1f})")
            else:
                self.statusBar().showMessage("⚠️ Intervalo muito pequeno. Cancelado.")

            self.mask_click_pt = None
            self._update_mask_table()
            self._plot_masking()

    def _on_mask_key_press(self, event):
        if event.key in ('escape', 'q'):
            self.mask_click_pt = None
            self._plot_masking()
            self.statusBar().showMessage("Seleção cancelada.")
        elif event.key == 'd' and event.xdata is not None:
            x = float(event.xdata)
            to_remove = [i for i, it in enumerate(self.spectral_mask.intervals) if it["low"] <= x <= it["upp"]]
            if to_remove:
                for idx in reversed(to_remove):
                    self.spectral_mask.remove_interval(idx)
                self._update_mask_table()
                self._plot_masking()
                self.statusBar().showMessage(f"🗑️ Máscara removida em {x:.1f} Å.")

    def _remove_selected_mask(self):
        row = self.tbl_masks.currentRow()
        if 0 <= row < len(self.spectral_mask.intervals):
            self.spectral_mask.remove_interval(row)
            self._update_mask_table()
            self._plot_masking()
            self.statusBar().showMessage("Região selecionada removida da máscara.")

    def _apply_mask_preset(self, preset):
        wl = self.proc_wl if self.proc_wl is not None else self.raw_wl
        wl_range = (wl[0], wl[-1]) if wl is not None and len(wl) > 0 else None
        self.spectral_mask = SpectralMask.from_preset(preset, wl_range=wl_range)
        self._update_mask_table()
        self._plot_masking()
        self.statusBar().showMessage(f"Preset '{preset.upper()}' carregado com sucesso ({len(self.spectral_mask.intervals)} intervalos).")

    def _clear_all_masks(self):
        self.spectral_mask.clear()
        self.mask_click_pt = None
        self._update_mask_table()
        self._plot_masking()
        self.statusBar().showMessage("Todas as máscaras foram removidas.")

    def _on_add_mask_interval(self):
        low = self.spin_mask_low.value()
        upp = self.spin_mask_upp.value()
        weight = self.spin_mask_weight.value()
        name = self.txt_mask_name.text().strip()
        self.spectral_mask.add_interval(low, upp, weight, name)
        self._update_mask_table()
        self._plot_masking()

    def _update_mask_table(self):
        self.tbl_masks.setRowCount(len(self.spectral_mask.intervals))
        for r, it in enumerate(self.spectral_mask.intervals):
            self.tbl_masks.setItem(r, 0, QTableWidgetItem(f"{it['low']:.1f}"))
            self.tbl_masks.setItem(r, 1, QTableWidgetItem(f"{it['upp']:.1f}"))
            self.tbl_masks.setItem(r, 2, QTableWidgetItem(f"{it['weight']:.1f}"))
            self.tbl_masks.setItem(r, 3, QTableWidgetItem(str(it['name'])))

    def _on_load_spectrum_for_masking_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Spectrum for Masking", "", "Spectra (*.spec *.txt *.dat *.csv *.fits);;All Files (*)"
        )
        if filepath:
            self.load_spectrum_for_masking(filepath)

    def load_spectrum_for_masking(self, filepath):
        try:
            wl, flx, eflx = load_spectrum(filepath)
            wl_c, flx_c, eflx_c = clean_spectrum(wl, flx, eflx)
            self.proc_wl, self.proc_flux, self.proc_eflux = wl_c, flx_c, eflx_c
            self.current_spectrum_path = filepath
            if hasattr(self, 'lbl_mask_loaded_file'):
                self.lbl_mask_loaded_file.setText(f"{os.path.basename(filepath)} ({len(wl_c)} pts)")
            if hasattr(self, 'lbl_loaded_file'):
                self.lbl_loaded_file.setText(f"{os.path.basename(filepath)} (loaded in Step 2)")
            self.statusBar().showMessage(f"Espectro carregado para mascaramento: {os.path.basename(filepath)} ({len(wl_c)} pontos)")
            self._plot_masking()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao carregar espectro", str(e))

    def _plot_masking(self, preserve_limits=True):
        cur_xlim = self.ax_mask.get_xlim() if preserve_limits and len(self.ax_mask.lines) > 0 else None
        cur_ylim = self.ax_mask.get_ylim() if preserve_limits and len(self.ax_mask.lines) > 0 else None

        self.ax_mask.cla()
        ax = self.ax_mask

        wl = self.proc_wl if self.proc_wl is not None else self.raw_wl
        flx = self.proc_flux if self.proc_flux is not None else self.raw_flux
        eflx = self.proc_eflux if self.proc_eflux is not None else self.raw_eflux

        if wl is not None and flx is not None:
            # 1. Base spectrum
            ax.plot(wl, flx, color="#0F172A", lw=1.2, label="Spectrum")
            if eflx is not None and len(eflx) == len(wl):
                ax.fill_between(wl, flx - eflx, flx + eflx, color="#93C5FD", alpha=0.3, label=r"Error ($\pm 1\sigma$)")

            # 2. Draw masked regions and highlight spectral segments (CreateMasks style)
            for idx, it in enumerate(self.spectral_mask.intervals):
                is_zero = (it["weight"] == 0.0)
                color = "#EF4444" if is_zero else "#10B981"
                alpha = 0.25 if is_zero else 0.20
                hatch = "//" if is_zero else None
                
                # Shaded vertical span
                ax.axvspan(it["low"], it["upp"], color=color, alpha=alpha, hatch=hatch)

                # Segment line highlight over spectrum (CreateMasks style!)
                mask_pts = (wl >= it["low"]) & (wl <= it["upp"])
                if np.any(mask_pts):
                    lbl = ("Weight 0 (Masked)" if is_zero else "Weight 2 (Feature)") if (idx == 0 or idx == 1) else None
                    ax.plot(wl[mask_pts], flx[mask_pts], color=color, lw=2.2, label=lbl)

            # 3. Draw 1st point guide line if user clicked
            if self.mask_click_pt is not None:
                ax.axvline(self.mask_click_pt, color="#DC2626", linestyle="--", lw=2, label=f"1st Point: {self.mask_click_pt:.1f} A")

            ax.legend(loc="upper right", frameon=True)
        else:
            ax.text(0.5, 0.5, "Nenhum espectro carregado no momento.\n\nClique no botao 'Load Spectrum' acima\nou pre-processe seu dado na Etapa 1.",
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, color="#64748B", fontsize=12)

        ax.set_xlabel(r"Wavelength ($\AA$)", fontsize=12)
        ax.set_ylabel("Flux", fontsize=12)
        ax.set_title("Spectral Mask Editor (CreateMasks Mode: Red = Weight 0, Green = Weight 2)", fontsize=13, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.5)

        if cur_xlim is not None and cur_xlim != (0.0, 1.0) and cur_ylim is not None and cur_ylim != (0.0, 1.0):
            ax.set_xlim(cur_xlim)
            ax.set_ylim(cur_ylim)
        else:
            if wl is not None and len(wl) > 1:
                ax.set_xlim(wl[0], wl[-1])
            self.toolbar_mask.update()

        self.canvas_mask.draw_idle()





    def _on_save_sm_dialog(self):
        default_name = "mask.mask"
        spec_path = getattr(self, 'current_spectrum_path', None)
        mask_dir = self.txt_mask_dir_step2.text().strip() if hasattr(self, 'txt_mask_dir_step2') else None
        mask_ext = self.starlight_config.mask_ext or ".mask"
        if not mask_ext.startswith('.'): mask_ext = "." + mask_ext
        if spec_path:
            spec_base = os.path.splitext(os.path.basename(spec_path))[0]
            if mask_dir:
                os.makedirs(mask_dir, exist_ok=True)
                default_name = os.path.join(mask_dir, f"{spec_base}{mask_ext}")
            else:
                spec_dir = os.path.dirname(spec_path)
                default_name = os.path.join(spec_dir, f"{spec_base}{mask_ext}") if spec_dir else f"{spec_base}{mask_ext}"

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save STARLIGHT Mask", default_name, "Starlight Mask (*.mask);;All Files (*)"
        )
        if filepath:
            self.spectral_mask.save_to_file(filepath)
            rel_mask = os.path.basename(filepath)
            self.starlight_config.mask_file = rel_mask
            if hasattr(self, 'txt_mask_file'):
                self.txt_mask_file.setText(rel_mask)
            QMessageBox.information(self, "Mask Saved", f"Máscara salva com sucesso em:\n{filepath}")

    def _on_open_sm_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Abrir Arquivo de Máscara STARLIGHT", "", "Starlight Mask (*.mask);;All Files (*)"
        )
        if filepath:
            self.spectral_mask = SpectralMask.load_from_file(filepath)
            self._update_mask_table()
            self._plot_masking()
            rel_mask = os.path.basename(filepath)
            self.starlight_config.mask_file = rel_mask
            if hasattr(self, 'txt_mask_file'):
                self.txt_mask_file.setText(rel_mask)



    # -------------------------------------------------------------
    # STEP 3: RUNNER PAGE
    # -------------------------------------------------------------
    def _create_step3_runner(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left control panel
        left_panel = QWidget()
        left_panel.setFixedWidth(460)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Paths Group
        grp_paths = QGroupBox("1. Paths & Executables")
        f_paths = QFormLayout(grp_paths)

        # Starlight Binary Executable
        row_exe = QHBoxLayout()
        self.txt_exe = QLineEdit(self.starlight_config.starlight_exe)
        btn_browse_exe = QPushButton("...")
        btn_browse_exe.setFixedWidth(36)
        btn_browse_exe.setToolTip("Selecionar Executável STARLIGHT")
        btn_browse_exe.clicked.connect(self._on_browse_exe)
        row_exe.addWidget(self.txt_exe)
        row_exe.addWidget(btn_browse_exe)
        f_paths.addRow("Starlight Binary:", row_exe)

        # Obs Spectra Dir with Browse button
        row_obs = QHBoxLayout()
        self.txt_obs_dir = QLineEdit(self.starlight_config.obs_dir)
        self.txt_obs_dir.setPlaceholderText("Pasta (ex: laura_major) ou padrão")
        btn_browse_obs = QPushButton("...")
        btn_browse_obs.setFixedWidth(36)
        btn_browse_obs.setToolTip("Selecionar Diretório dos Espectros Observados")
        btn_browse_obs.clicked.connect(self._on_browse_obs_dir)
        row_obs.addWidget(self.txt_obs_dir)
        row_obs.addWidget(btn_browse_obs)
        f_paths.addRow("Obs Spectra Dir:", row_obs)

        # Spectrum File Extension / Pattern Filter
        self.combo_spec_ext = QComboBox()
        self.combo_spec_ext.setEditable(True)
        self.combo_spec_ext.addItems(["*.spec", "*.txt", "*.dat", "*.csv", "*", "*.fits"])
        self.combo_spec_ext.setCurrentText(self.starlight_config.data_ext or "*.spec")
        f_paths.addRow("Spectrum Extension / Pattern:", self.combo_spec_ext)

        # Masks Directory with Browse button
        row_mask_dir = QHBoxLayout()
        self.txt_mask_dir_step3 = QLineEdit(self.starlight_config.mask_dir if hasattr(self.starlight_config, 'mask_dir') else "")
        self.txt_mask_dir_step3.setPlaceholderText("Folder with .mask files")
        btn_browse_mask_dir = QPushButton("...")
        btn_browse_mask_dir.setFixedWidth(36)
        btn_browse_mask_dir.clicked.connect(self._on_browse_mask_dir_step3)
        row_mask_dir.addWidget(self.txt_mask_dir_step3)
        row_mask_dir.addWidget(btn_browse_mask_dir)
        f_paths.addRow("Masks Directory:", row_mask_dir)
        self.txt_mask_dir_step3.textChanged.connect(self._sync_mask_dirs)

        # Mask Extension
        self.txt_mask_ext = QLineEdit(self.starlight_config.mask_ext)
        self.txt_mask_ext.setPlaceholderText(".mask")
        f_paths.addRow("Mask Extension:", self.txt_mask_ext)

        # Configuration File with Browse button
        row_config = QHBoxLayout()
        self.txt_config_file = QLineEdit(self.starlight_config.config_file)
        btn_browse_config = QPushButton("...")
        btn_browse_config.setFixedWidth(36)
        btn_browse_config.setToolTip("Selecionar Arquivo de Configuration (.config)")
        btn_browse_config.clicked.connect(self._on_browse_config_file)
        row_config.addWidget(self.txt_config_file)
        row_config.addWidget(btn_browse_config)
        f_paths.addRow("Configuration File:", row_config)

        # Bases Directory with Browse button
        row_base_dir = QHBoxLayout()
        self.txt_base_dir = QLineEdit(self.starlight_config.base_dir)
        btn_browse_base_dir = QPushButton("...")
        btn_browse_base_dir.setFixedWidth(36)
        btn_browse_base_dir.setToolTip("Selecionar Diretório das Populações Base")
        btn_browse_base_dir.clicked.connect(self._on_browse_base_dir)
        row_base_dir.addWidget(self.txt_base_dir)
        row_base_dir.addWidget(btn_browse_base_dir)
        f_paths.addRow("Bases Directory:", row_base_dir)

        # Base Manifest File with Browse button
        row_base_file = QHBoxLayout()
        self.txt_base_file = QLineEdit(self.starlight_config.base_file)
        btn_browse_base_file = QPushButton("...")
        btn_browse_base_file.setFixedWidth(36)
        btn_browse_base_file.setToolTip("Selecionar Arquivo Base Manifest (ex: BasesXSLKrupaPCRR, BaseHRpyPopStarChab)")
        btn_browse_base_file.clicked.connect(self._on_browse_base_file)
        row_base_file.addWidget(self.txt_base_file)
        row_base_file.addWidget(btn_browse_base_file)
        f_paths.addRow("Base Manifest File:", row_base_file)

        # Output Directory with Browse button
        row_out = QHBoxLayout()
        self.txt_out_dir = QLineEdit(self.starlight_config.out_dir)
        btn_browse_out_dir = QPushButton("...")
        btn_browse_out_dir.setFixedWidth(36)
        btn_browse_out_dir.setToolTip("Selecionar Diretório de Saída dos Resultados")
        btn_browse_out_dir.clicked.connect(self._on_browse_out_dir)
        row_out.addWidget(self.txt_out_dir)
        row_out.addWidget(btn_browse_out_dir)
        f_paths.addRow("Output Directory:", row_out)

        left_layout.addWidget(grp_paths)





        # Fit Parameters Group
        grp_pars = QGroupBox("2. Synthesis Parameters")
        f_pars = QFormLayout(grp_pars)

        self.spin_fit_ini = QDoubleSpinBox()
        self.spin_fit_ini.setRange(100.0, 50000.0)
        self.spin_fit_ini.setValue(self.starlight_config.olsyn_ini)
        f_pars.addRow("Fit λ Lower (Å):", self.spin_fit_ini)

        self.spin_fit_fin = QDoubleSpinBox()
        self.spin_fit_fin.setRange(100.0, 50000.0)
        self.spin_fit_fin.setValue(self.starlight_config.olsyn_fin)
        f_pars.addRow("Fit λ Upper (Å):", self.spin_fit_fin)

        self.spin_sn_low = QDoubleSpinBox()
        self.spin_sn_low.setRange(100.0, 50000.0)
        self.spin_sn_low.setValue(self.starlight_config.llow_sn)
        f_pars.addRow("S/N Window Lower (Å):", self.spin_sn_low)

        self.spin_sn_upp = QDoubleSpinBox()
        self.spin_sn_upp.setRange(100.0, 50000.0)
        self.spin_sn_upp.setValue(self.starlight_config.lupp_sn)
        f_pars.addRow("S/N Window Upper (Å):", self.spin_sn_upp)

        self.combo_kinematics = QComboBox()
        self.combo_kinematics.addItems(["FIT", "FXK"])
        f_pars.addRow("Kinematics:", self.combo_kinematics)

        self.spin_procs = QSpinBox()
        self.spin_procs.setRange(1, os.cpu_count() or 4)
        self.spin_procs.setValue(min(4, os.cpu_count() or 4))
        f_pars.addRow("Parallel CPU Cores:", self.spin_procs)

        left_layout.addWidget(grp_pars)



        btn_generate_grids = QPushButton("Generate Grid Files (grid_*.inp)")
        btn_generate_grids.clicked.connect(self._on_generate_grids)
        left_layout.addWidget(btn_generate_grids)

        self.btn_run_starlight = QPushButton("Run STARLIGHT")
        self.btn_run_starlight.setStyleSheet("background-color: #10B981; color: white; font-size: 14px;")
        self.btn_run_starlight.clicked.connect(self._on_run_starlight_clicked)
        left_layout.addWidget(self.btn_run_starlight)

        left_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(380)
        scroll_area.setMaximumWidth(520)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(left_panel)

        # Right Log & Progress Area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        lbl_log = QLabel("Execution Console & Diagnostics")
        lbl_log.setStyleSheet("font-weight: 700; font-size: 14px;")
        right_layout.addWidget(lbl_log)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        right_layout.addWidget(self.progress_bar)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("""
            background-color: #0F172A;
            color: #38BDF8;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            border-radius: 6px;
            padding: 8px;
        """)
        right_layout.addWidget(self.txt_log, 1)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(scroll_area)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        return page


    def _to_relpath(self, path):
        if not path:
            return ""
        path = str(path).strip()
        try:
            cwd = os.getcwd()
            rel = os.path.relpath(path, cwd)
            if not rel.startswith(".."):
                return rel
            return path
        except Exception:
            return path

    def _on_browse_exe(self):
        f, _ = QFileDialog.getOpenFileName(self, "Selecionar Executável STARLIGHT", self.txt_exe.text(), "All Files (*)")
        if f:
            rel = self._to_relpath(f)
            self.txt_exe.setText(rel)
            self.starlight_config.starlight_exe = rel

    def _on_browse_obs_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Selecionar Diretório dos Espectros Observados", self.txt_obs_dir.text())
        if d:
            rel = self._to_relpath(d)
            self.txt_obs_dir.setText(rel)
            self.starlight_config.obs_dir = rel


    def _on_browse_mask_dir_step2(self):
        d = QFileDialog.getExistingDirectory(self, "Select Masks Directory")
        if d:
            self.txt_mask_dir_step2.setText(self._to_relpath(d))

    def _on_browse_mask_dir_step3(self):
        d = QFileDialog.getExistingDirectory(self, "Select Masks Directory")
        if d:
            self.txt_mask_dir_step3.setText(self._to_relpath(d))

    def _sync_mask_dirs(self, text):
        sender = self.sender()
        if sender == getattr(self, 'txt_mask_dir_step2', None) and hasattr(self, 'txt_mask_dir_step3'):
            self.txt_mask_dir_step3.blockSignals(True)
            self.txt_mask_dir_step3.setText(text)
            self.txt_mask_dir_step3.blockSignals(False)
        elif sender == getattr(self, 'txt_mask_dir_step3', None) and hasattr(self, 'txt_mask_dir_step2'):
            self.txt_mask_dir_step2.blockSignals(True)
            self.txt_mask_dir_step2.setText(text)
            self.txt_mask_dir_step2.blockSignals(False)
        self.starlight_config.mask_dir = text

    def _on_browse_mask_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo de Máscara STARLIGHT", self.txt_mask_file.text(), "All Files (*);;Starlight Mask (*.mask)")
        if f:
            rel = os.path.basename(f) if os.path.dirname(os.path.abspath(f)) == os.getcwd() else self._to_relpath(f)
            self.txt_mask_file.setText(rel)
            self.starlight_config.mask_file = rel

    def _on_browse_config_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo de Configuration (.config)", self.txt_config_file.text(), "All Files (*);;Config Files (*.config)")
        if f:
            rel = os.path.basename(f)
            self.txt_config_file.setText(rel)
            self.starlight_config.config_file = rel

    def _on_browse_base_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Selecionar Diretório das Populações Base", self.txt_base_dir.text())
        if d:
            rel = self._to_relpath(d)
            self.txt_base_dir.setText(rel)
            self.starlight_config.base_dir = rel

    def _on_browse_base_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo Base Manifest (ex: BasesXSLKrupaPCRR, BaseHRpyPopStarChab)", self.txt_base_file.text(), "All Files (*)")
        if f:
            rel = os.path.basename(f)
            self.txt_base_file.setText(rel)
            self.starlight_config.base_file = rel

    def _on_browse_out_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Selecionar Diretório de Saída dos Resultados", self.txt_out_dir.text())
        if d:
            rel = self._to_relpath(d)
            self.txt_out_dir.setText(rel)
            self.starlight_config.out_dir = rel



    def _sync_config_from_ui(self):
        self.starlight_config.starlight_exe = self.txt_exe.text().strip()
        self.starlight_config.obs_dir = self.txt_obs_dir.text().strip()
        self.starlight_config.data_ext = self.combo_spec_ext.currentText().strip()
        self.starlight_config.config_file = self.txt_config_file.text().strip()
        self.starlight_config.mask_ext = self.txt_mask_ext.text().strip()
        self.starlight_config.base_dir = self.txt_base_dir.text().strip()
        self.starlight_config.base_file = self.txt_base_file.text().strip()
        self.starlight_config.out_dir = self.txt_out_dir.text().strip()
        self.starlight_config.olsyn_ini = self.spin_fit_ini.value()
        self.starlight_config.olsyn_fin = self.spin_fit_fin.value()
        self.starlight_config.llow_sn = self.spin_sn_low.value()
        self.starlight_config.lupp_sn = self.spin_sn_upp.value()
        self.starlight_config.kinematics = self.combo_kinematics.currentText()
        self.starlight_config.procs = self.spin_procs.value()


    def _resolve_spectrum_files(self, raw_input, ext_pattern="*.spec"):
        raw_input = (raw_input or "").strip()
        ext_pattern = (ext_pattern or "*.spec").strip()
        if not ext_pattern.startswith("*") and not ext_pattern.startswith("."):
            ext_pattern = f"*.{ext_pattern}"
        elif ext_pattern.startswith(".") and not ext_pattern.startswith("*"):
            ext_pattern = f"*{ext_pattern}"

        if not raw_input:
            raw_input = "."

        ignored_exts = ('.mask', '.config', '.inp', '.out', '.base', '.py', '.pyc', '.sh', '.md', '.png', '.pdf')

        # 1. If raw_input is a glob pattern (contains * or ?)
        if '*' in raw_input or '?' in raw_input:
            files = sorted(glob.glob(raw_input))
            valid = [f for f in files if os.path.isfile(f) and not f.endswith(ignored_exts)]
            if valid:
                dir_part = os.path.dirname(raw_input) or "."
                return valid, dir_part

        # 2. If raw_input is an existing directory
        if os.path.isdir(raw_input):
            if ext_pattern == "*":
                spec_files = [
                    os.path.join(raw_input, f) for f in sorted(os.listdir(raw_input))
                    if os.path.isfile(os.path.join(raw_input, f)) and not f.endswith(ignored_exts)
                ]
            else:
                spec_files = sorted(glob.glob(os.path.join(raw_input, ext_pattern)))
            
            if spec_files:
                return spec_files, raw_input

            # Fallback if specific extension didn't match: search other common spectrum formats
            for alt_ext in ("*.spec", "*.txt", "*.dat", "*.csv"):
                found = sorted(glob.glob(os.path.join(raw_input, alt_ext)))
                valid = [f for f in found if not f.endswith(ignored_exts)]
                if valid:
                    return valid, raw_input

            all_f = [
                os.path.join(raw_input, f) for f in sorted(os.listdir(raw_input))
                if os.path.isfile(os.path.join(raw_input, f)) and not f.endswith(ignored_exts)
            ]
            if all_f:
                return all_f, raw_input

        # 3. If raw_input is a single file
        if os.path.isfile(raw_input):
            return [raw_input], os.path.dirname(raw_input) or "."

        # 4. Fallback search (e.g. folder name typed without slashes)
        pattern = f"{raw_input}/{ext_pattern}" if ext_pattern != "*" else f"{raw_input}/*"
        found = sorted(glob.glob(pattern))
        valid = [f for f in found if os.path.isfile(f) and not f.endswith(ignored_exts)]
        if valid:
            return valid, raw_input

        # 5. Check local directory
        if ext_pattern == "*":
            local_files = [f for f in sorted(os.listdir(".")) if os.path.isfile(f) and not f.endswith(ignored_exts)]
            if local_files:
                return local_files, "."
        else:
            local_spec = sorted(glob.glob(ext_pattern))
            if local_spec:
                return local_spec, "."

        return [], raw_input


    def _on_save_config_state(self):
        import json
        self._sync_config_from_ui()
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration State", "starlight_gui_config.json", "JSON Files (*.json);;All Files (*)"
        )
        if filepath:
            try:
                state = {
                    "exe": self.txt_exe.text(),
                    "obs_dir": self.txt_obs_dir.text(),
                    "spec_ext": self.combo_spec_ext.currentText(),
                    "mask_dir": self.txt_mask_dir_step3.text() if hasattr(self, 'txt_mask_dir_step3') else "",
                    "mask_ext": self.txt_mask_ext.text(),
                    "config_file": self.txt_config_file.text(),
                    "base_dir": self.txt_base_dir.text(),
                    "base_file": self.txt_base_file.text(),
                    "out_dir": self.txt_out_dir.text(),
                    "fit_ini": self.spin_fit_ini.value(),
                    "fit_fin": self.spin_fit_fin.value(),
                    "sn_low": self.spin_sn_low.value(),
                    "sn_upp": self.spin_sn_upp.value(),
                    "kinematics": self.combo_kinematics.currentText(),
                    "procs": self.spin_procs.value(),
                    "z": self.spin_z.value(),
                    "law": self.combo_law.currentText(),
                    "av": self.spin_av.value(),
                    "rv": self.spin_rv.value(),
                    "rebin_step": self.spin_rebin_step.value()
                }
                with open(filepath, 'w') as f:
                    json.dump(state, f, indent=4)
                QMessageBox.information(self, "Config Saved", f"Configuration state saved to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save config: {e}")

    def _on_load_config_state(self):
        import json
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration State", "", "JSON Files (*.json);;All Files (*)"
        )
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    state = json.load(f)
                
                self.txt_exe.setText(state.get("exe", ""))
                self.txt_obs_dir.setText(state.get("obs_dir", ""))
                self.combo_spec_ext.setCurrentText(state.get("spec_ext", "*.spec"))
                if hasattr(self, 'txt_mask_dir_step3'): self.txt_mask_dir_step3.setText(state.get("mask_dir", ""))
                self.txt_mask_ext.setText(state.get("mask_ext", ".mask"))
                self.txt_config_file.setText(state.get("config_file", ""))
                self.txt_base_dir.setText(state.get("base_dir", ""))
                self.txt_base_file.setText(state.get("base_file", ""))
                self.txt_out_dir.setText(state.get("out_dir", ""))
                
                if "fit_ini" in state: self.spin_fit_ini.setValue(state["fit_ini"])
                if "fit_fin" in state: self.spin_fit_fin.setValue(state["fit_fin"])
                if "sn_low" in state: self.spin_sn_low.setValue(state["sn_low"])
                if "sn_upp" in state: self.spin_sn_upp.setValue(state["sn_upp"])
                if "kinematics" in state: self.combo_kinematics.setCurrentText(state["kinematics"])
                if "procs" in state: self.spin_procs.setValue(state["procs"])
                
                self._sync_config_from_ui()
                self.statusBar().showMessage(f"Config loaded from {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load config: {e}")


    def _validate_bases(self):
        base_file = self.txt_base_file.text().strip()
        base_dir = self.txt_base_dir.text().strip()
        
        if not base_file or not os.path.exists(base_file):
            return False, f"Base Manifest File not found: {base_file}"
            
        if not base_dir or not os.path.exists(base_dir):
            return False, f"Bases Directory not found: {base_dir}"
            
        missing_files = []
        try:
            with open(base_file, 'r') as f:
                lines = f.readlines()
                
            is_first_line = True
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                tokens = line.split()
                if is_first_line:
                    if len(tokens) <= 2 and tokens[0].isdigit():
                        is_first_line = False
                        continue
                    is_first_line = False
                
                base_filename = tokens[0]
                if not os.path.exists(os.path.join(base_dir, base_filename)):
                    missing_files.append(base_filename)
                    
            if missing_files:
                err_msg = f"Found {len(missing_files)} missing base files in '{base_dir}'.\n\nFirst few missing:\n"
                for m in missing_files[:5]:
                    err_msg += f"- {m}\n"
                if len(missing_files) > 5:
                    err_msg += "..."
                return False, err_msg
                
            return True, "All base files present."
        except Exception as e:
            return False, f"Error validating bases: {str(e)}"

    def _on_generate_grids(self):
        self._sync_config_from_ui()
        raw_obs = self.txt_obs_dir.text().strip()
        ext_pattern = self.combo_spec_ext.currentText().strip()
        spec_files, obs_dir = self._resolve_spectrum_files(raw_obs, ext_pattern)

        if not spec_files:
            QMessageBox.warning(
                self,
                "Nenhum Espectro Encontrado",
                f"Nenhum arquivo de espectro correspondente a '{ext_pattern}' foi encontrado em:\n'{raw_obs}'"
            )
            return

        self.starlight_config.obs_dir = obs_dir

        is_valid, msg = self._validate_bases()
        if not is_valid:
            QMessageBox.critical(self, "Bases Validation Failed", msg)
            return

        try:
            grids = generate_grid_files(spec_files, self.starlight_config)
            self.txt_log.append(f"✅ Gerado(s) {len(grids)} arquivo(s) de grade para {len(spec_files)} espectro(s) em '{obs_dir}' ({ext_pattern}):")
            for g in grids:
                self.txt_log.append(f"   • {g}")
            for spec in spec_files:
                self.txt_log.append(f"      - {os.path.basename(spec)}")
            QMessageBox.information(
                self,
                "Grades Geradas",
                f"Sucesso! Foram gerados {len(grids)} arquivo(s) de grade (grid_*.inp) para {len(spec_files)} espectro(s) encontrados em:\n{obs_dir}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro na Geração de Grades", str(e))




    def _on_run_starlight_clicked(self):
        reply = QMessageBox.question(
            self,
            "Gerar Grids e Salvar?",
            "Deseja gerar novos arquivos de Grid e salvar a configuração Global antes de rodar o STARLIGHT?\n(Isso previne que você rode o modelo com configurações velhas).",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Cancel:
            return
        elif reply == QMessageBox.Yes:
            self._on_generate_grids()
            self._on_save_config_state()

        grid_files = sorted(glob.glob("grid_*.inp"))
        if not grid_files:
            QMessageBox.warning(self, "No Grid Files", "Please generate or create grid_*.inp files first.")
            return

        self._sync_config_from_ui()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(grid_files))

        self.worker_thread = StarlightWorkerThread(
            grid_files,
            self.starlight_config.starlight_exe,
            cwd="."
        )
        self.worker_thread.grid_finished.connect(self._on_grid_finished)
        self.worker_thread.log_message.connect(self.txt_log.append)
        self.worker_thread.all_finished.connect(self._on_all_starlight_finished)

        self.btn_run_starlight.setEnabled(False)
        self.worker_thread.start()

    def _on_grid_finished(self, result):
        val = self.progress_bar.value() + 1
        self.progress_bar.setValue(val)

    def _on_all_starlight_finished(self):
        self.btn_run_starlight.setEnabled(True)
        self.txt_log.append("STARLIGHT batch completed.")
        self.statusBar().showMessage("STARLIGHT batch finished.")
        QMessageBox.information(self, "Finished", "STARLIGHT run finished! Check Results tab to analyze fits.")

    # -------------------------------------------------------------
    # STEP 4: RESULTS PAGE
    # -------------------------------------------------------------
    def _create_step4_results(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left control / Metrics panel
        left_panel = QWidget()
        left_panel.setFixedWidth(380)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # File Select
        grp_out = QGroupBox("1. Select Starlight Fit (.out)")
        f_out = QVBoxLayout(grp_out)
        btn_open_out = QPushButton("Abrir Resultado (.out)")
        btn_open_out.clicked.connect(self._on_open_out_dialog)
        self.lbl_out_file = QLabel("No fit loaded")
        self.lbl_out_file.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        f_out.addWidget(btn_open_out)
        f_out.addWidget(self.lbl_out_file)
        left_layout.addWidget(grp_out)

        # Metric Summary Cards
        grp_metrics = QGroupBox("2. Fit Metrics & Physical Properties")
        f_met = QFormLayout(grp_metrics)
        self.lbl_chi2 = QLabel("—")
        self.lbl_adev = QLabel("—")
        self.lbl_snr = QLabel("—")
        self.lbl_av = QLabel("—")
        self.lbl_v0 = QLabel("—")
        self.lbl_vd = QLabel("—")
        self.lbl_age_l = QLabel("—")
        self.lbl_age_m = QLabel("—")
        self.lbl_z_l = QLabel("—")
        self.lbl_z_m = QLabel("—")

        f_met.addRow("Reduced χ²:", self.lbl_chi2)
        f_met.addRow("adev (%):", self.lbl_adev)
        f_met.addRow("S/N in Window:", self.lbl_snr)
        f_met.addRow("Dust A_V (mag):", self.lbl_av)
        f_met.addRow("Velocity v_0 (km/s):", self.lbl_v0)
        f_met.addRow("Dispersion σ_d (km/s):", self.lbl_vd)
        f_met.addRow("⟨log t_*⟩_L (yr):", self.lbl_age_l)
        f_met.addRow("⟨log t_*⟩_M (yr):", self.lbl_age_m)
        f_met.addRow("⟨Z_*⟩_L (Z_sun):", self.lbl_z_l)
        f_met.addRow("⟨Z_*⟩_M (Z_sun):", self.lbl_z_m)
        left_layout.addWidget(grp_metrics)

        # Export Buttons
        btn_save_plot = QPushButton("Exportar Gráficos (PNG/PDF)")
        btn_save_plot.clicked.connect(self._on_export_figures)
        left_layout.addWidget(btn_save_plot)

        btn_save_table = QPushButton("Exportar Tabela (.csv)")
        btn_save_table.clicked.connect(self._on_export_table)
        left_layout.addWidget(btn_save_table)


        left_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(360)
        scroll_area.setMaximumWidth(500)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(left_panel)

        # Right Plots
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.fig_results = Figure(figsize=(9, 8), tight_layout=True)
        self.canvas_results = FigureCanvas(self.fig_results)
        self.toolbar_results = NavigationToolbar(self.canvas_results, self)

        right_layout.addWidget(self.toolbar_results)
        right_layout.addWidget(self.canvas_results)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(scroll_area)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        return page


    def _on_open_out_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open STARLIGHT Output", "", "Starlight Output (*.out);;All Files (*)"
        )
        if filepath:
            self.load_starlight_out(filepath)

    def load_starlight_out(self, filepath):
        try:
            # Use the PyLight standard reader
            pars, ParList, popin, popend, syntin, version = starlightPars(filepath)
            pop, popComps = popVectors(filepath)
            spec = StSyntesis(filepath)
            
            # Save raw arrays so _plot_results can use them
            self.parsed_output = {
                'pars': pars,
                'ParList': ParList,
                'pop': pop,
                'popComps': popComps,
                'spec': spec,
                'filename': os.path.basename(filepath)
            }
            self.lbl_out_file.setText(os.path.basename(filepath))

            # Map parameters by name from ParList
            # ParList in V5 is e.g., ['[chi2/Nl_eff', 'chi2]', 'flux_unit]', 'fobs_norm', 'Lobs_norm', 'LumDistInMpc', '[adev (%)]', ...]
            # We find the indices dynamically
            def get_par(name):
                for i, p in enumerate(ParList):
                    if name in p: return pars[i]
                return np.nan

            chi2 = get_par('chi2/Nl_eff')
            if np.isnan(chi2): chi2 = get_par('chi2]')
            adev = get_par('adev')
            snr = get_par('S/N in S/N window')
            av = get_par('AV_min')
            v0 = get_par('v0_min')
            vd = get_par('vd_min')

            # Calculate mean ages and metallicities from pop arrays
            # pop columns: 0=x_j(%), 1=Mini_j(%), 2=Mcor_j(%), 3=age_j(yr), 4=Z_j, 5=(L/M)_j, 6=j
            x_j = pop[:, 0]
            mcor_j = pop[:, 2]
            age_yr = pop[:, 3]
            log_age = np.log10(np.where(age_yr > 0, age_yr, 1))
            Z_j = pop[:, 4]
            
            tot_x = np.sum(x_j)
            tot_m = np.sum(mcor_j)
            
            mean_log_age_l = np.sum(x_j * log_age) / tot_x if tot_x > 0 else np.nan
            mean_z_l = np.sum(x_j * Z_j) / tot_x if tot_x > 0 else np.nan
            
            mean_log_age_m = np.sum(mcor_j * log_age) / tot_m if tot_m > 0 else np.nan
            mean_z_m = np.sum(mcor_j * Z_j) / tot_m if tot_m > 0 else np.nan

            # Update Labels
            self.lbl_chi2.setText(f"{chi2:.3f}" if not np.isnan(chi2) else "—")
            self.lbl_adev.setText(f"{adev:.2f}%" if not np.isnan(adev) else "—")
            self.lbl_snr.setText(f"{snr:.1f}" if not np.isnan(snr) else "—")
            self.lbl_av.setText(f"{av:.3f}" if not np.isnan(av) else "—")
            self.lbl_v0.setText(f"{v0:.1f}" if not np.isnan(v0) else "—")
            self.lbl_vd.setText(f"{vd:.1f}" if not np.isnan(vd) else "—")
            self.lbl_age_l.setText(f"{mean_log_age_l:.2f}" if not np.isnan(mean_log_age_l) else "—")
            self.lbl_age_m.setText(f"{mean_log_age_m:.2f}" if not np.isnan(mean_log_age_m) else "—")
            self.lbl_z_l.setText(f"{mean_z_l:.4f}" if not np.isnan(mean_z_l) else "—")
            self.lbl_z_m.setText(f"{mean_z_m:.4f}" if not np.isnan(mean_z_m) else "—")

            self._plot_results()
            self.statusBar().showMessage(f"Loaded fit: {os.path.basename(filepath)}")
        except Exception as e:
            QMessageBox.critical(self, "Error Reading .out File", str(e))

    def _plot_results(self):
        self.fig_results.clear()
        if self.parsed_output is None:
            self.canvas_results.draw()
            return

        data = self.parsed_output
        spec = data['spec']
        pop = data['pop']
        filename = data['filename']
        
        if len(spec) == 0:
            self.canvas_results.draw()
            return

        # 2 Subplots: Top = Spectrum Fit & Residuals; Bottom = Population Vectors (x_j & m_j)
        gs = self.fig_results.add_gridspec(3, 2, height_ratios=[2.5, 1.0, 1.8], hspace=0.3)
        ax_top = self.fig_results.add_subplot(gs[0, :])
        ax_res = self.fig_results.add_subplot(gs[1, :], sharex=ax_top)
        ax_pop_x = self.fig_results.add_subplot(gs[2, 0])
        ax_pop_m = self.fig_results.add_subplot(gs[2, 1])

        # Columns for StSyntesis: 0:l_obs, 1:f_obs, 2:f_syn, 3:wei
        l_obs = spec[:, 0]
        f_obs = spec[:, 1]
        f_syn = spec[:, 2]
        wei = spec[:, 3]
        
        residual = f_obs - f_syn

        # Top Plot: Observed vs Synthetic
        ax_top.plot(l_obs, f_obs, color="#0F172A", lw=1.1, label="Observed")
        ax_top.plot(l_obs, f_syn, color="#DC2626", lw=1.3, label="STARLIGHT Synthetic")

        # Flag masked points in gray
        import numpy as np
        mask_idx = wei <= 0.0
        if np.any(mask_idx):
            ax_top.scatter(l_obs[mask_idx], f_obs[mask_idx], color="#94A3B8", s=6, label="Masked (w=0)")

        ax_top.set_ylabel("Flux (Normalized)", fontsize=11)
        
        # We need chi2 and adev to show in title
        chi2 = 0; adev = 0
        for i, p in enumerate(data['ParList']):
            if 'chi2/Nl_eff' in p or 'chi2]' in p: chi2 = data['pars'][i]
            if 'adev' in p: adev = data['pars'][i]
            
        ax_top.set_title(f"STARLIGHT Fit: {filename} ($\chi^2$={chi2:.2f}, adev={adev:.2f}%)", fontsize=12, fontweight="bold")
        ax_top.legend(loc="upper right", frameon=True)
        ax_top.grid(True, linestyle="--", alpha=0.4)

        # Residuals Plot
        ax_res.plot(l_obs, residual, color="#2563EB", lw=1.0)
        ax_res.axhline(0, color="#64748B", linestyle="--", lw=1.0)
        ax_res.set_xlabel("Wavelength ($\AA$)", fontsize=11)
        ax_res.set_ylabel("Resid (O-S)", fontsize=10)
        ax_res.grid(True, linestyle="--", alpha=0.4)

        # Bottom Left: Light Fractions (x_j)
        if len(pop) > 0:
            x_vals = pop[:, 0]
            m_vals = pop[:, 2]

            ax_pop_x.bar(np.arange(len(x_vals)), x_vals, color="#3B82F6", edgecolor="#1D4ED8", width=0.7)
            ax_pop_x.set_ylabel("Light Fraction x_j (%)", fontsize=10)
            ax_pop_x.set_xlabel("SSP Index", fontsize=10)
            
            # Simple Age fractions logic
            age_yr = pop[:, 3]
            x_young = np.sum(x_vals[age_yr <= 1.0e8])
            x_interm = np.sum(x_vals[(age_yr > 1.0e8) & (age_yr <= 2.0e9)])
            x_old = np.sum(x_vals[age_yr > 2.0e9])
            
            ax_pop_x.set_title(f"Light SFH (Young={x_young:.1f}%, Interm={x_interm:.1f}%, Old={x_old:.1f}%)", fontsize=11)
            ax_pop_x.grid(True, linestyle="--", alpha=0.4)

            # Bottom Right: Mass Fractions (m_j)
            ax_pop_m.bar(np.arange(len(m_vals)), m_vals, color="#10B981", edgecolor="#047857", width=0.7)
            ax_pop_m.set_ylabel("Mass Fraction m_j (%)", fontsize=10)
            ax_pop_m.set_xlabel("SSP Index", fontsize=10)
            
            m_young = np.sum(m_vals[age_yr <= 1.0e8])
            m_interm = np.sum(m_vals[(age_yr > 1.0e8) & (age_yr <= 2.0e9)])
            m_old = np.sum(m_vals[age_yr > 2.0e9])
            ax_pop_m.set_title(f"Mass SFH (Young={m_young:.1f}%, Interm={m_interm:.1f}%, Old={m_old:.1f}%)", fontsize=11)
            
            ax_pop_m.grid(True, linestyle="--", alpha=0.4)

        self.canvas_results.draw()

    def _on_export_figures(self):
        if self.parsed_output is None:
            QMessageBox.warning(self, "No Fit Loaded", "Please load a .out file first.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Figure", f"{os.path.splitext(self.parsed_output.filename)[0]}_fit.png",
            "PNG Image (*.png);;PDF Document (*.pdf);;SVG Vector (*.svg)"
        )
        if out_path:
            self.fig_results.savefig(out_path, dpi=200, bbox_inches='tight')
            QMessageBox.information(self, "Figure Saved", f"Saved: {out_path}")

    def _on_export_table(self):
        if self.parsed_output is None:
            QMessageBox.warning(self, "No Fit Loaded", "Please load a .out file first.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Parameters Table", f"{os.path.splitext(self.parsed_output.filename)[0]}_summary.csv",
            "CSV Table (*.csv);;TXT Table (*.txt)"
        )
        if out_path:
            import pandas as pd
            # Make a simple dict out of pars
            out_d = {'file': self.parsed_output['filename']}
            for i, p in enumerate(self.parsed_output['ParList']):
                out_d[p] = self.parsed_output['pars'][i]
            df = pd.DataFrame([out_d])
            df.to_csv(out_path, index=False)
            QMessageBox.information(self, "Table Saved", f"Saved: {out_path}")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
