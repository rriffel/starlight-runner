"""Auto-generated mixin module for Starlight Runner GUI."""
import sys, os, glob, json, re, traceback
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .constants import (
    ACCENT, ACCENT_HOVER, DARK_BG, CARD_BG, TEXT_COLOR,
    MUTED, BORDER_COLOR, SUCCESS_COLOR, DANGER_COLOR, STYLESHEET
)

from ..reddening import REDDENING_LAWS
from ..preprocessing import load_spectrum, clean_spectrum, save_spec_file
from ..masking import SpectralMask, OPTICAL_EMISSION_LINES, NIR_EMISSION_AND_TELLURIC_LINES
from ..custom_widgets import InteractiveMaskDialog

class MaskingMixin:
    def _on_open_detached_mask_dialog(self):
        wl = self.proc_wl if self.proc_wl is not None else self.raw_wl
        flx = self.proc_flux if self.proc_flux is not None else self.raw_flux
        eflx = self.proc_eflux if self.proc_eflux is not None else self.raw_eflux

        if wl is None or flx is None:
            QMessageBox.warning(self, "No Spectrum", "Please load or preprocess a spectrum first.")
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
                self.statusBar().showMessage(f"Mask editing finished ({len(self.spectral_mask.intervals)} intervals).")




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
        btn_load_spec_mask = QPushButton("Load Spectrum (.spec, .txt, .fits)")
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
        grp_interactive = QGroupBox("2. Interactive Masking (CreateMasks Mode)")
        f_inter = QVBoxLayout(grp_interactive)
        f_inter.setSpacing(8)

        self.btn_mask_interactive = QPushButton("Interactive Mode: Mask on Plot")
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

        btn_detach_mask = QPushButton("Detached Mask Window (Full Screen)")
        btn_detach_mask.setStyleSheet("background-color: #4F46E5; color: white; font-weight: bold; padding: 8px; font-size: 13px;")
        btn_detach_mask.clicked.connect(self._on_open_detached_mask_dialog)
        f_inter.addWidget(btn_detach_mask)

        # Weight selection for Left-Click
        weight_row = QHBoxLayout()
        weight_row.addWidget(QLabel("Click Weight:"))
        self.rb_weight_0 = QRadioButton("🔴 Weight 0.0 (Exclude)")
        self.rb_weight_0.setChecked(True)
        self.rb_weight_2 = QRadioButton("🟢 Weight 2.0 (Emphasize)")
        weight_row.addWidget(self.rb_weight_0)
        weight_row.addWidget(self.rb_weight_2)
        f_inter.addLayout(weight_row)

        lbl_mask_help = QLabel(
            "<b>Right-Click</b>: 1st and 2nd click masks region with Weight 0.0 (Red)<br>"
            "<b>Middle-Click</b>: 1st and 2nd click masks region with Weight 2.0 (Green)<br>"
            "<b>Left-Click</b>: Zoom/Pan (or Mask when Interactive Mode is active)<br>"
            "<b>Key 'd'</b>: Hover over a mask region and press 'd' to delete it<br>"
            "<b>Key 'Esc'</b>: Cancels 1st point selection"
        )
        lbl_mask_help.setWordWrap(True)
        lbl_mask_help.setStyleSheet("color: #475569; font-size: 11px; line-height: 1.3; background: #F1F5F9; padding: 6px; border-radius: 4px;")
        f_inter.addWidget(lbl_mask_help)
        left_layout.addWidget(grp_interactive)

        # 2. Presets Group
        grp_presets = QGroupBox("3. Mask Presets")
        f_pre = QVBoxLayout(grp_presets)

        btn_opt_preset = QPushButton("Load Optical Preset (CreateMasks)")
        btn_opt_preset.clicked.connect(lambda: self._apply_mask_preset("optical"))
        f_pre.addWidget(btn_opt_preset)

        btn_nir_preset = QPushButton("Load NIR Preset")
        btn_nir_preset.clicked.connect(lambda: self._apply_mask_preset("nir"))
        f_pre.addWidget(btn_nir_preset)

        btn_clear_masks = QPushButton("Clear All Masks")
        btn_clear_masks.setStyleSheet("background-color: #EF4444; color: white;")
        btn_clear_masks.clicked.connect(self._clear_all_masks)
        f_pre.addWidget(btn_clear_masks)

        left_layout.addWidget(grp_presets)

        # 3. Manual Interval Group
        grp_add = QGroupBox("4. Add Mask Region Manually")
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

        btn_add_interval = QPushButton("+ Add Region")
        btn_add_interval.clicked.connect(self._on_add_mask_interval)
        f_add.addRow(btn_add_interval)
        left_layout.addWidget(grp_add)

        # 4. Mask Table
        self.tbl_masks = QTableWidget(0, 4)
        self.tbl_masks.setHorizontalHeaderLabels(["Low (Å)", "Upp (Å)", "Weight", "Label"])
        self.tbl_masks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_masks.setMinimumHeight(130)
        left_layout.addWidget(self.tbl_masks, 1)

        btn_del_mask = QPushButton("Remove Selected Region")
        btn_del_mask.clicked.connect(self._remove_selected_mask)
        left_layout.addWidget(btn_del_mask)

        # I/O Buttons
        io_row = QHBoxLayout()
        btn_load_sm = QPushButton("Open Mask (.mask)")
        btn_load_sm.clicked.connect(self._on_open_sm_dialog)
        btn_save_sm = QPushButton("Save Mask (.mask)")
        btn_save_sm.clicked.connect(self._on_save_sm_dialog)
        io_row.addWidget(btn_load_sm)
        io_row.addWidget(btn_save_sm)
        left_layout.addLayout(io_row)

        btn_next_step3 = QPushButton("Advance to Step 3 (STARLIGHT Grid)  ➔")
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
            self.btn_mask_interactive.setText("🟢 Interactive Mask Mode ACTIVE")
            self.statusBar().showMessage("Interactive Mask Mode Active: Click 1st and 2nd endpoints on the spectrum to mask.")
        else:
            self.btn_mask_interactive.setText("✂️ Interactive Mode: Mask on Plot")
            self.statusBar().showMessage("Interactive Mask Mode Deactivated.")
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
            self.statusBar().showMessage(f"📍 1st point at {clicked_x:.1f} Å. Click 2nd point to apply mask with weight {w_txt} (or 'Esc' to cancel).")
            self._plot_masking()
        else:
            p1 = float(min(self.mask_click_pt, clicked_x))
            p2 = float(max(self.mask_click_pt, clicked_x))
            w = self.mask_click_weight if hasattr(self, 'mask_click_weight') else weight

            if (p2 - p1) > 1.0:
                name = "Mask (Weight 0)" if w == 0.0 else "Key Feature (Weight 2)"
                self.spectral_mask.add_interval(p1, p2, weight=w, name=name)
                self.statusBar().showMessage(f"✅ Masked region added: {p1:.1f} - {p2:.1f} Å (weight={w:.1f})")
            else:
                self.statusBar().showMessage("⚠️ Interval too small. Cancelled.")

            self.mask_click_pt = None
            self._update_mask_table()
            self._plot_masking()

    def _on_mask_key_press(self, event):
        if event.key in ('escape', 'q'):
            self.mask_click_pt = None
            self._plot_masking()
            self.statusBar().showMessage("Selection cancelled.")
        elif event.key == 'd' and event.xdata is not None:
            x = float(event.xdata)
            to_remove = [i for i, it in enumerate(self.spectral_mask.intervals) if it["low"] <= x <= it["upp"]]
            if to_remove:
                for idx in reversed(to_remove):
                    self.spectral_mask.remove_interval(idx)
                self._update_mask_table()
                self._plot_masking()
                self.statusBar().showMessage(f"🗑️ Mask removed at {x:.1f} Å.")

    def _remove_selected_mask(self):
        row = self.tbl_masks.currentRow()
        if 0 <= row < len(self.spectral_mask.intervals):
            self.spectral_mask.remove_interval(row)
            self._update_mask_table()
            self._plot_masking()
            self.statusBar().showMessage("Selected region removed from mask.")

    def _apply_mask_preset(self, preset):
        wl = self.proc_wl if self.proc_wl is not None else self.raw_wl
        wl_range = (wl[0], wl[-1]) if wl is not None and len(wl) > 0 else None
        self.spectral_mask = SpectralMask.from_preset(preset, wl_range=wl_range)
        self._update_mask_table()
        self._plot_masking()
        self.statusBar().showMessage(f"Preset '{preset.upper()}' loaded successfully ({len(self.spectral_mask.intervals)} intervals).")

    def _clear_all_masks(self):
        self.spectral_mask.clear()
        self.mask_click_pt = None
        self._update_mask_table()
        self._plot_masking()
        self.statusBar().showMessage("All masks removed.")

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
            self.statusBar().showMessage(f"Spectrum loaded for masking: {os.path.basename(filepath)} ({len(wl_c)} points)")
            self._plot_masking()
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Spectrum", str(e))

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
            ax.text(0.5, 0.5, "No spectrum loaded.\n\nClick 'Load Spectrum' above\nor preprocess data in Step 1.",
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
            QMessageBox.information(self, "Mask Saved", f"Mask saved successfully to:\n{filepath}")

    def _on_open_sm_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open STARLIGHT Mask File", "", "Starlight Mask (*.mask);;All Files (*)"
        )
        if filepath:
            self.spectral_mask = SpectralMask.load_from_file(filepath)
            self._update_mask_table()
            self._plot_masking()
            rel_mask = os.path.basename(filepath)
            self.starlight_config.mask_file = rel_mask
            if hasattr(self, 'txt_mask_file'):
                self.txt_mask_file.setText(rel_mask)
