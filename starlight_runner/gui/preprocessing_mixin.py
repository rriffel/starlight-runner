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

from ..reddening import REDDENING_LAWS, deredden
from ..preprocessing import (
    load_spectrum, clean_spectrum, apply_redshift,
    rebin_spectrum, exclude_spectral_regions,
    trim_spectral_bounds, save_spec_file, DEFAULT_TELLURIC_REGIONS
)
from ..masking import SpectralMask
from ..custom_widgets import InteractiveCutDialog

class PreprocessingMixin:
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
        btn_next_step2.clicked.connect(self._on_advance_to_step2)
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
            if self.toolbar_preproc.mode == 'zoom rect':
                self.toolbar_preproc.zoom()
            elif self.toolbar_preproc.mode == 'pan/zoom':
                self.toolbar_preproc.pan()
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



    def _on_advance_to_step2(self):
        wl = self.proc_wl if self.proc_wl is not None else self.raw_wl
        flx = self.proc_flux if self.proc_flux is not None else self.raw_flux
        if wl is not None and flx is not None:
            reply = QMessageBox.question(
                self,
                "Salvar Espectro Processado",
                "Deseja salvar o espectro (.spec) pré-processado antes de avançar para a Etapa 2?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                saved = self._on_export_spec_dialog(auto_advance=False)
                if saved:
                    self.set_active_page(1)
            elif reply == QMessageBox.No:
                self.set_active_page(1)
            # If Cancel, do nothing
        else:
            self.set_active_page(1)

    def _on_export_spec_dialog(self, auto_advance=True):
        wl = self.proc_wl if self.proc_wl is not None else self.raw_wl
        flx = self.proc_flux if self.proc_flux is not None else self.raw_flux
        eflx = self.proc_eflux if self.proc_eflux is not None else self.raw_eflux

        if wl is None or flx is None:
            QMessageBox.warning(self, "Sem Dados", "Nenhum dado de espectro para exportar.")
            return False

        default_name = "spectrum_clean.spec"
        if self.current_spectrum_path:
            base = os.path.splitext(os.path.basename(self.current_spectrum_path))[0]
            default_name = f"{base}_clean.spec"

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Arquivo STARLIGHT .spec", default_name, "STARLIGHT Spec (*.spec);;All Files (*)"
        )
        if out_path:
            save_spec_file(out_path, wl, flx, eflx)
            self.current_spectrum_path = out_path
            if hasattr(self, 'lbl_mask_loaded_file'):
                self.lbl_mask_loaded_file.setText(f"{os.path.basename(out_path)} ({len(wl)} pts)")

            if auto_advance:
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
            else:
                self.statusBar().showMessage(f"Salvo: {out_path}")
            return True
        return False

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
