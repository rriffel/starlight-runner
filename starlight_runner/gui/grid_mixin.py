"""Auto-generated mixin module for Starlight Runner GUI."""
import sys, os, glob, json, re, traceback, copy
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from . import constants

from ..runner import (StarlightConfig, generate_grid_files, read_config_norm, config_for_norm,
                      write_config_with_norm, norm_from_window, base_metallicities,
                      NORM_NIR, NORM_OPTICAL)
from ..spectrum_io import needs_conversion, DEFAULT_CONVERTED_DIR
from ..custom_widgets import StarlightWorkerThread
from ..montecarlo import (
    prepare_monte_carlo, cleanup_mc_spectra, load_mc_outputs, mc_statistics, write_mc_table,
    error_spectrum_problem
)

class GridMixin:
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
        btn_browse_exe.setToolTip("Select STARLIGHT Executable")
        btn_browse_exe.clicked.connect(self._on_browse_exe)
        row_exe.addWidget(self.txt_exe)
        row_exe.addWidget(btn_browse_exe)
        f_paths.addRow("Starlight Binary:", row_exe)

        # Obs Spectra Dir with Browse button
        row_obs = QHBoxLayout()
        self.txt_obs_dir = QLineEdit(self.starlight_config.obs_dir)
        self.txt_obs_dir.setPlaceholderText("Folder (e.g. laura_major) or pattern")
        btn_browse_obs = QPushButton("...")
        btn_browse_obs.setFixedWidth(36)
        btn_browse_obs.setToolTip("Select Observed Spectra Directory")
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

        # Standard mask: the same mask file for every spectrum
        self.chk_std_mask = QCheckBox("Use standard mask (same for all spectra)")
        self.chk_std_mask.setToolTip(
            "Every spectrum uses the chosen mask file instead of <spectrum><mask extension>\n"
            "from the Masks Directory (also for the Monte Carlo realizations)."
        )
        f_paths.addRow("Standard Mask:", self.chk_std_mask)
        row_std_mask = QHBoxLayout()
        self.txt_std_mask = QLineEdit("")
        self.txt_std_mask.setPlaceholderText("Mask file used for all spectra")
        self.btn_std_mask = QPushButton("Choose…")
        self.btn_std_mask.clicked.connect(self._on_choose_std_mask)
        row_std_mask.addWidget(self.txt_std_mask)
        row_std_mask.addWidget(self.btn_std_mask)
        f_paths.addRow("", row_std_mask)
        self.chk_std_mask.toggled.connect(self._on_toggle_std_mask)
        self._on_toggle_std_mask(False)

        # Configuration File with Browse button
        row_config = QHBoxLayout()
        self.txt_config_file = QLineEdit(self.starlight_config.config_file)
        btn_browse_config = QPushButton("...")
        btn_browse_config.setFixedWidth(36)
        btn_browse_config.setToolTip("Select Configuration File (.config)")
        btn_browse_config.clicked.connect(self._on_browse_config_file)
        row_config.addWidget(self.txt_config_file)
        row_config.addWidget(btn_browse_config)
        f_paths.addRow("Configuration File:", row_config)

        # Bases Directory with Browse button
        row_base_dir = QHBoxLayout()
        self.txt_base_dir = QLineEdit(self.starlight_config.base_dir)
        btn_browse_base_dir = QPushButton("...")
        btn_browse_base_dir.setFixedWidth(36)
        btn_browse_base_dir.setToolTip("Select Base Populations Directory")
        btn_browse_base_dir.clicked.connect(self._on_browse_base_dir)
        row_base_dir.addWidget(self.txt_base_dir)
        row_base_dir.addWidget(btn_browse_base_dir)
        f_paths.addRow("Bases Directory:", row_base_dir)

        # Base File with Browse button
        row_base_file = QHBoxLayout()
        self.txt_base_file = QLineEdit(self.starlight_config.base_file)
        btn_browse_base_file = QPushButton("...")
        btn_browse_base_file.setFixedWidth(36)
        btn_browse_base_file.setToolTip("Select Base File (e.g. BasesXSLKrupaPCRR, BaseHRpyPopStarChab)")
        btn_browse_base_file.clicked.connect(self._on_browse_base_file)
        row_base_file.addWidget(self.txt_base_file)
        row_base_file.addWidget(btn_browse_base_file)
        f_paths.addRow("Base File:", row_base_file)
        self.txt_base_file.editingFinished.connect(self._sync_pylight_zs)

        # Output Directory with Browse button
        row_out = QHBoxLayout()
        self.txt_out_dir = QLineEdit(self.starlight_config.out_dir)
        btn_browse_out_dir = QPushButton("...")
        btn_browse_out_dir.setFixedWidth(36)
        btn_browse_out_dir.setToolTip("Select Output Directory")
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


        # Normalization window = S/N window: the same two values go to the grid
        # (llow_SN, lupp_SN) and to the .config (llow_norm, lupp_norm);
        # l_norm of the bases is their mean.
        norm = read_config_norm(self.starlight_config.config_file) or NORM_NIR
        self.spin_l_norm = QDoubleSpinBox()
        self.spin_l_norm.setRange(100.0, 50000.0)
        self.spin_l_norm.setReadOnly(True)
        self.spin_l_norm.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin_l_norm.setToolTip("[l_norm] normalization lambda of the base spectra (.config):\n"
                                    "always the mean of the observed normalization window, (llow_norm + lupp_norm) / 2")
        f_pars.addRow("Norm λ for Bases (Å):", self.spin_l_norm)
        self.spin_llow_norm = QDoubleSpinBox()
        self.spin_llow_norm.setRange(100.0, 50000.0)
        self.spin_llow_norm.setValue(norm[1])
        self.spin_llow_norm.setToolTip("Lower limit of the normalization window of the observed spectrum:\n"
                                       "[llow_norm] in the .config and [llow_SN] (S/N window) in the grid")
        f_pars.addRow("Norm Window Lower (Å):", self.spin_llow_norm)
        self.spin_lupp_norm = QDoubleSpinBox()
        self.spin_lupp_norm.setRange(100.0, 50000.0)
        self.spin_lupp_norm.setValue(norm[2])
        self.spin_lupp_norm.setToolTip("Upper limit of the normalization window of the observed spectrum:\n"
                                       "[lupp_norm] in the .config and [lupp_SN] (S/N window) in the grid.\n"
                                       "If they differ from the .config you are asked, when generating grids,\n"
                                       "whether to update it; otherwise a copy is written in starlight_input/.")
        f_pars.addRow("Norm Window Upper (Å):", self.spin_lupp_norm)
        for w in (self.spin_llow_norm, self.spin_lupp_norm):
            w.valueChanged.connect(self._update_l_norm)
        self._update_l_norm()
        self.txt_config_file.editingFinished.connect(self._sync_norm_from_config_file)

        self.combo_kinematics = QComboBox()
        self.combo_kinematics.addItems(["FIT", "FXK"])
        f_pars.addRow("Kinematics:", self.combo_kinematics)

        self.chk_err_spec = QCheckBox("Error spectrum available")
        self.chk_err_spec.setChecked(bool(self.starlight_config.is_err_available))
        self.chk_err_spec.setToolTip("[IsErrSpecAvailable] 1/0 = Yes/No")
        f_pars.addRow("Error Spectrum:", self.chk_err_spec)

        self.chk_flag_spec = QCheckBox("Flag spectrum available")
        self.chk_flag_spec.setChecked(bool(self.starlight_config.is_flag_available))
        self.chk_flag_spec.setToolTip("[IsFlagSpecAvailable] 1/0 = Yes/No")
        f_pars.addRow("Flag Spectrum:", self.chk_flag_spec)

        self.spin_seed = QSpinBox()
        self.spin_seed.setRange(1, 2147483647)
        self.spin_seed.setValue(self.starlight_config.seed)
        self.spin_seed.setToolTip("[your phone number] — Random seed for the Markov Chain fits")
        f_pars.addRow("Seed (phone number):", self.spin_seed)

        self.spin_procs = QSpinBox()
        self.spin_procs.setRange(1, os.cpu_count() or 4)
        self.spin_procs.setValue(min(4, os.cpu_count() or 4))
        f_pars.addRow("Parallel CPU Cores:", self.spin_procs)

        # Monte Carlo errors: N perturbed copies of each spectrum, same setup and mask
        row_mc = QHBoxLayout()
        self.chk_mc = QCheckBox("Monte Carlo errors")
        self.chk_mc.setToolTip(
            "Also fit N realizations of each spectrum, with the flux perturbed within its errors,\n"
            "using this same setup and the spectrum's mask. Every property is then reported\n"
            "as the mean ± std of the N fits (Step 4 and <MC dir>/<spectrum>/<spectrum>_mc_props.csv)."
        )
        self.spin_mc_n = QSpinBox()
        self.spin_mc_n.setRange(2, 100000)
        self.spin_mc_n.setValue(100)
        row_mc.addWidget(self.chk_mc)
        row_mc.addWidget(QLabel("N:"))
        row_mc.addWidget(self.spin_mc_n, 1)
        f_pars.addRow("Uncertainties:", row_mc)

        row_mc_dir = QHBoxLayout()
        self.txt_mc_dir = QLineEdit("./mcmc")
        self.txt_mc_dir.setToolTip("Simulation directory: <dir>/<spectrum>/spec (perturbed spectra),\n"
                                   "<dir>/<spectrum>/out (fits) and the mean ± std table.")
        self.btn_mc_dir = QPushButton("...")
        self.btn_mc_dir.setFixedWidth(36)
        self.btn_mc_dir.clicked.connect(self._on_browse_mc_dir)
        row_mc_dir.addWidget(self.txt_mc_dir)
        row_mc_dir.addWidget(self.btn_mc_dir)
        f_pars.addRow("MC Directory:", row_mc_dir)

        self.chk_mc_keep = QCheckBox("Keep perturbed spectra")
        self.chk_mc_keep.setToolTip("If unchecked, the N simulated spectra are removed after the run\n"
                                    "(the fits and the mean ± std table are always kept).")
        f_pars.addRow("", self.chk_mc_keep)

        for wdg in (self.spin_mc_n, self.txt_mc_dir, self.btn_mc_dir, self.chk_mc_keep):
            wdg.setEnabled(False)
            self.chk_mc.toggled.connect(wdg.setEnabled)

        # Monte Carlo needs an error spectrum: only available when the input has one
        self._mc_tooltip = self.chk_mc.toolTip()
        self.chk_err_spec.toggled.connect(self._update_mc_availability)
        self.txt_obs_dir.editingFinished.connect(self._update_mc_availability)
        self.combo_spec_ext.currentTextChanged.connect(self._update_mc_availability)
        self._update_mc_availability()

        left_layout.addWidget(grp_pars)



        btn_generate_grids = QPushButton("Generate Grid Files (grid_*.inp)")
        btn_generate_grids.clicked.connect(self._on_generate_grids)
        left_layout.addWidget(btn_generate_grids)

        btn_run_layout = QHBoxLayout()
        self.btn_run_starlight = QPushButton("Run STARLIGHT")
        self.btn_run_starlight.setStyleSheet("background-color: #10B981; color: white; font-size: 14px; font-weight: bold; padding: 6px;")
        self.btn_run_starlight.clicked.connect(self._on_run_starlight_clicked)

        self.btn_stop_starlight = QPushButton("Stop")
        self.btn_stop_starlight.setStyleSheet("background-color: #EF4444; color: white; font-size: 14px; font-weight: bold; padding: 6px;")
        self.btn_stop_starlight.setEnabled(False)
        self.btn_stop_starlight.clicked.connect(self._on_stop_starlight_clicked)

        btn_run_layout.addWidget(self.btn_run_starlight, 3)
        btn_run_layout.addWidget(self.btn_stop_starlight, 1)
        left_layout.addLayout(btn_run_layout)

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
        f, _ = QFileDialog.getOpenFileName(self, "Select STARLIGHT Executable", self.txt_exe.text(), "All Files (*)")
        if f:
            rel = self._to_relpath(f)
            self.txt_exe.setText(rel)
            self.starlight_config.starlight_exe = rel

    def _on_browse_obs_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Observed Spectra Directory", self.txt_obs_dir.text())
        if d:
            rel = self._to_relpath(d)
            self.txt_obs_dir.setText(rel)
            self.starlight_config.obs_dir = rel
            self._update_mc_availability()


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

    def _update_l_norm(self, *_):
        """l_norm (bases) = mean of the observed normalization window."""
        self.spin_l_norm.setValue(norm_from_window(self.spin_llow_norm.value(), self.spin_lupp_norm.value())[0])

    def _sync_pylight_zs(self, *_):
        """PyLight metallicities (Zs) = unique Z values of the Step 3 Base File."""
        zs = base_metallicities(self.txt_base_file.text().strip()) if hasattr(self, 'txt_base_file') else []
        if zs:
            self.pylight_config["Zs"] = zs
            self.pylight_config["Zs_source"] = self.txt_base_file.text().strip()
        return zs

    def _sync_norm_from_config_file(self, *_):
        """
        Show the normalization window of the chosen .config in Step 3 (l_norm
        follows as its mean). Differences with the file are only reported when
        grids are generated / STARLIGHT is run (_check_norm_against_config).
        """
        norm = read_config_norm(self.txt_config_file.text().strip())
        if norm and hasattr(self, 'spin_l_norm'):
            self.spin_llow_norm.setValue(norm[1])
            self.spin_lupp_norm.setValue(norm[2])
            self._update_l_norm()

    def _current_norm(self):
        return (self.spin_l_norm.value(), self.spin_llow_norm.value(), self.spin_lupp_norm.value())

    def _check_norm_against_config(self, reason=""):
        """
        Compare the Step 3 normalization with the chosen .config. If they
        differ, show the .config values and ask whether to write the Step 3
        values into it (a .bak copy is kept). If not, the file is left as it
        is (grids then use a copy in starlight_input/) and the same values
        are not asked again. Returns True if the .config matches afterwards.
        """
        if not hasattr(self, 'spin_l_norm'):
            return True
        path = self.txt_config_file.text().strip()
        file_norm = read_config_norm(path) if path else None
        if file_norm is None:
            return True
        cur = self._current_norm()
        if all(abs(a - b) < 1e-6 for a, b in zip(file_norm, cur)):
            return True
        file_mean = norm_from_window(file_norm[1], file_norm[2])[0]
        if abs(file_norm[0] - file_mean) > 1e-6:
            reason = (reason + "\n" if reason else "") + (
                f"Note: in the configuration file l_norm = {file_norm[0]:.1f} Å is not the mean of its "
                f"normalization window ({file_norm[1]:.1f}-{file_norm[2]:.1f} Å → {file_mean:.1f} Å).")
        if getattr(self, '_norm_declined', None) == (os.path.abspath(path), cur):
            return False

        reply = QMessageBox.question(
            self, "Normalization differs from the configuration file",
            (f"{reason}\n\n" if reason else "")
            + f"Configuration file: {path}\n"
            f"   l_norm = {file_norm[0]:.1f} Å   llow_norm = {file_norm[1]:.1f} Å   lupp_norm = {file_norm[2]:.1f} Å\n\n"
            f"Step 3 (Synthesis Parameters):\n"
            f"   l_norm = {cur[0]:.1f} Å   llow_norm = {cur[1]:.1f} Å   lupp_norm = {cur[2]:.1f} Å\n\n"
            "(l_norm of the bases = mean of the normalization window.)\n\n"
            "Update the configuration file with the Step 3 values?\n"
            "(Yes: the file is rewritten, a copy is kept as .bak.\n"
            " No: the file is not changed; the grids use a copy with the Step 3 values.)",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            try:
                import shutil
                shutil.copyfile(path, path + ".bak")
                write_config_with_norm(path, path, *cur)
                self._norm_declined = None
                msg = f"Configuration file updated: {path} (backup {path}.bak)"
                self.statusBar().showMessage(msg)
                if hasattr(self, 'txt_log'):
                    self.txt_log.append(f"📐 {msg} — normalization {cur}")
                return True
            except Exception as e:
                QMessageBox.critical(self, "Configuration file", f"Could not update {path}:\n{e}")
                return False
        self._norm_declined = (os.path.abspath(path), cur)
        return False

    def _apply_synthesis_preset(self, kind, wl_range=None):
        """
        Step 3 defaults for a Step 2 mask preset. Fit range = spectrum start + 50 Å
        to end - 50 Å (spectrum saved in Step 1). NIR keeps the standard
        windows (S/N & normalization 12200-12250 Å, l_norm 12225 Å); optical
        normalizes (and measures S/N) at 5650-5750 Å, l_norm 5700 Å.
        Returns a short description of what was set.
        """
        if not hasattr(self, 'spin_fit_ini'):
            return ""
        kind = (kind or "").lower()
        norm = NORM_OPTICAL if kind == "optical" else NORM_NIR
        done = []
        if wl_range is not None and wl_range[1] - wl_range[0] > 100.0:
            lo, hi = float(wl_range[0]) + 50.0, float(wl_range[1]) - 50.0
            self.spin_fit_ini.setValue(lo)
            self.spin_fit_fin.setValue(hi)
            done.append(f"fit {lo:.0f}-{hi:.0f} Å")
        self.spin_llow_norm.setValue(norm[1])
        self.spin_lupp_norm.setValue(norm[2])
        self._update_l_norm()
        done.append(f"normalization (S/N) window {norm[1]:.0f}-{norm[2]:.0f} Å, l_norm {norm[0]:.0f} Å")
        if wl_range is not None and not (wl_range[0] <= norm[1] and norm[2] <= wl_range[1]):
            done.append(f"⚠️ normalization window outside the spectrum ({wl_range[0]:.0f}-{wl_range[1]:.0f} Å)")
        self._sync_config_from_ui()
        return "; ".join(done)

    def _effective_config(self):
        """
        Copy of the run configuration with the normalization of the Step 3
        fields: if it differs from the .config, a copy of the .config with it
        is written in starlight_input/ and used (the original is not modified).
        """
        cfg = copy.deepcopy(self.starlight_config)
        if hasattr(self, 'spin_l_norm') and os.path.isfile(cfg.config_file):
            cfg.config_file = config_for_norm(cfg.config_file, self._current_norm(), DEFAULT_CONVERTED_DIR)
        return cfg

    def _on_toggle_std_mask(self, checked):
        """Standard mask on: choose one file; per-spectrum mask folder/extension are not used."""
        self.txt_std_mask.setEnabled(checked)
        self.btn_std_mask.setEnabled(checked)
        self.txt_mask_dir_step3.setEnabled(not checked)
        self.txt_mask_ext.setEnabled(not checked)
        if checked and not self.txt_std_mask.text().strip():
            self._on_choose_std_mask()
            if not self.txt_std_mask.text().strip():
                self.chk_std_mask.setChecked(False)

    def _on_choose_std_mask(self):
        start = self.txt_std_mask.text().strip() or self.txt_mask_dir_step3.text().strip() or "."
        f, _ = QFileDialog.getOpenFileName(
            self, "Choose the Standard Mask (used for all spectra)", start,
            "Starlight Mask (*.mask *.gm *.msk);;All Files (*)"
        )
        if f:
            self.txt_std_mask.setText(self._to_relpath(f))

    def _standard_mask_file(self):
        """Path of the standard mask if that option is on, else None (raises if missing)."""
        if not (hasattr(self, 'chk_std_mask') and self.chk_std_mask.isChecked()):
            return None
        path = self.txt_std_mask.text().strip()
        if not path:
            raise ValueError("'Use standard mask' is on but no mask file was chosen.")
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Standard mask not found: {path}")
        return path

    def _on_browse_config_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Configuration File (.config)", self.txt_config_file.text(), "All Files (*);;Config Files (*.config)")
        if f:
            # relative path: the grid quotes it when the file is in another folder
            rel = self._to_relpath(f)
            self.txt_config_file.setText(rel)
            self.starlight_config.config_file = rel
            self._sync_norm_from_config_file()

    def _on_browse_base_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Base Populations Directory", self.txt_base_dir.text())
        if d:
            rel = self._to_relpath(d)
            self.txt_base_dir.setText(rel)
            self.starlight_config.base_dir = rel

    def _on_browse_base_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Base File (e.g. BasesXSLKrupaPCRR, BaseHRpyPopStarChab)", self.txt_base_file.text(), "All Files (*)")
        if f:
            # relative path: the grid quotes it when the file is in another folder
            rel = self._to_relpath(f)
            self.txt_base_file.setText(rel)
            self.starlight_config.base_file = rel
            self._sync_pylight_zs()

    def _on_browse_out_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.txt_out_dir.text())
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
        # S/N window of the grid = normalization window
        self.starlight_config.llow_sn = self.spin_llow_norm.value()
        self.starlight_config.lupp_sn = self.spin_lupp_norm.value()
        self.starlight_config.kinematics = self.combo_kinematics.currentText()
        self.starlight_config.is_err_available = 1 if self.chk_err_spec.isChecked() else 0
        self.starlight_config.is_flag_available = 1 if self.chk_flag_spec.isChecked() else 0
        self.starlight_config.seed = self.spin_seed.value()
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
    def _validate_bases(self):
        base_file = self.txt_base_file.text().strip()
        base_dir = self.txt_base_dir.text().strip()
        
        if not base_file or not os.path.exists(base_file):
            return False, f"Base File not found: {base_file}"
            
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
                "No Spectra Found",
                f"No spectrum files matching '{ext_pattern}' were found in:\n'{raw_obs}'"
            )
            return

        self.starlight_config.obs_dir = obs_dir

        is_valid, msg = self._validate_bases()
        if not is_valid:
            QMessageBox.critical(self, "Bases Validation Failed", msg)
            return

        try:
            std_mask = self._standard_mask_file()
            self._check_norm_against_config("Generating grids.")
            cfg = self._effective_config()
            if cfg.config_file != self.starlight_config.config_file:
                self.txt_log.append(f"📐 Normalization {self._current_norm()} → using {cfg.config_file}")
            if std_mask:
                # STARLIGHT reads <mask_dir>/<mask name>: point mask_dir to the standard mask's folder
                cfg.mask_dir = os.path.dirname(std_mask) or "."
            grids = generate_grid_files(spec_files, cfg, default_mask_file=std_mask)
            if std_mask:
                self.txt_log.append(f"🎭 Standard mask for all spectra: {std_mask}")
            n_conv = sum(needs_conversion(f) for f in spec_files)
            if n_conv:
                self.txt_log.append(
                    f"🔄 {n_conv} spectrum(a) (CSV/header) converted to STARLIGHT ASCII .spec in "
                    f"'{DEFAULT_CONVERTED_DIR}/' (used as obs_dir in the grids)."
                )
            self.txt_log.append(f"✅ Generated {len(grids)} grid file(s) for {len(spec_files)} spectrum(a) in '{obs_dir}' ({ext_pattern}):")
            for g in grids:
                self.txt_log.append(f"   • {g}")
            for spec in spec_files:
                self.txt_log.append(f"      - {os.path.basename(spec)}")
            QMessageBox.information(
                self,
                "Grids Generated",
                f"Success! Generated {len(grids)} grid file(s) (grid_*.inp) for {len(spec_files)} spectrum(a) found in:\n{obs_dir}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Grid Generation Error", str(e))




    def _on_run_starlight_clicked(self):
        reply = QMessageBox.question(
            self,
            "Generate Grids & Save Config?",
            "Do you want to generate fresh Grid files and save the Global configuration before running STARLIGHT?\n(Recommended to avoid running with outdated parameters).",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Cancel:
            return
        self._check_norm_against_config("Running STARLIGHT.")
        if reply == QMessageBox.Yes:
            self._on_generate_grids()
            self._on_save_config_state()

        grid_files = sorted(glob.glob("grid_*.inp"))
        self._mc_jobs = []
        if self.chk_mc.isChecked():
            mc_grids = self._prepare_mc_grids()
            if mc_grids is None:
                return
            grid_files += mc_grids

        if not grid_files:
            QMessageBox.warning(self, "No Grid Files", "Please generate or create grid_*.inp files first.")
            return

        self._sync_config_from_ui()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(grid_files))

        self.worker_thread = StarlightWorkerThread(
            grid_files,
            self.starlight_config.starlight_exe,
            cwd=".",
            max_workers=self.starlight_config.procs
        )
        self.worker_thread.grid_finished.connect(self._on_grid_finished)
        self.worker_thread.log_message.connect(self.txt_log.append)
        self.worker_thread.all_finished.connect(self._on_all_starlight_finished)

        self.btn_run_starlight.setEnabled(False)
        self.btn_stop_starlight.setEnabled(True)
        self.worker_thread.start()

    def _mc_unavailable_reason(self, check_all=False):
        """Why Monte Carlo cannot run on the current input (None if it can)."""
        if not self.chk_err_spec.isChecked():
            return "the input has no error spectrum ('Error spectrum available' is unchecked)"
        spec_files, _ = self._resolve_spectrum_files(
            self.txt_obs_dir.text().strip(), self.combo_spec_ext.currentText().strip()
        )
        if not spec_files:
            return "no input spectrum found"
        for spec in (spec_files if check_all else spec_files[:3]):
            problem = error_spectrum_problem(spec)
            if problem:
                return problem
        return None

    def _update_mc_availability(self, *_):
        """Enable the Monte Carlo option only when the input spectra have an error spectrum."""
        if not hasattr(self, 'chk_mc'):
            return
        reason = self._mc_unavailable_reason()
        if reason:
            self.chk_mc.setChecked(False)
            self.chk_mc.setEnabled(False)
            self.chk_mc.setToolTip(f"Monte Carlo errors need an error spectrum: {reason}.")
        else:
            self.chk_mc.setEnabled(True)
            self.chk_mc.setToolTip(self._mc_tooltip)

    def _on_browse_mc_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Monte Carlo Simulation Directory", self.txt_mc_dir.text())
        if d:
            self.txt_mc_dir.setText(self._to_relpath(d))

    def _prepare_mc_grids(self):
        """
        Create N Monte Carlo realizations of every spectrum of this run, each one
        sharing the mask of its spectrum, and their grid files (mc_grid_*.inp).
        Returns the grid files, or None if the run should be aborted.
        """
        self._sync_config_from_ui()
        spec_files, obs_dir = self._resolve_spectrum_files(
            self.txt_obs_dir.text().strip(), self.combo_spec_ext.currentText().strip()
        )
        if not spec_files:
            QMessageBox.warning(self, "Monte Carlo", "No spectrum found for the Monte Carlo realizations.")
            return None

        reason = self._mc_unavailable_reason(check_all=True)
        if reason:
            QMessageBox.critical(self, "Monte Carlo", f"Monte Carlo errors need an error spectrum:\n{reason}.")
            self._update_mc_availability()
            return None

        cfg = self._effective_config()
        n = self.spin_mc_n.value()
        try:
            std_mask = self._standard_mask_file()
        except Exception as e:
            QMessageBox.critical(self, "Monte Carlo", str(e))
            return None
        mask_ext = cfg.mask_ext if cfg.mask_ext.startswith('.') else f".{cfg.mask_ext}"
        masks = {
            s: std_mask or os.path.join(cfg.mask_dir or ".", os.path.splitext(os.path.basename(s))[0] + mask_ext)
            for s in spec_files
        }
        missing = [m for m in masks.values() if not os.path.exists(m)]
        if missing:
            QMessageBox.critical(
                self, "Monte Carlo — Missing Masks",
                "Each spectrum needs its mask for the Monte Carlo realizations. Not found:\n"
                + "\n".join(missing[:10]) + ("\n..." if len(missing) > 10 else "")
            )
            return None

        reply = QMessageBox.question(
            self, "Monte Carlo",
            f"Monte Carlo errors: {len(spec_files)} spectrum(a) × {n} realizations = "
            f"{len(spec_files) * n} additional STARLIGHT fits.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return None

        mc_dir = self.txt_mc_dir.text().strip() or "./mcmc"
        grids = []
        try:
            for spec in spec_files:
                job = prepare_monte_carlo(spec, cfg, n, mask_file=masks[spec], mc_dir=mc_dir)
                self._mc_jobs.append(job)
                grids += job['grids']
                self.txt_log.append(
                    f"🎲 Monte Carlo: {n} realizations of {os.path.basename(spec)} "
                    f"(mask {os.path.basename(masks[spec])}) → {job['root']}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Monte Carlo Error", str(e))
            for job in self._mc_jobs:
                cleanup_mc_spectra(job)
            self._mc_jobs = []
            return None
        return grids

    def _finish_mc(self):
        """
        Aggregate each Monte Carlo set: mean ± std table and final plot (mean
        values with std error bars), saved next to the fits and shown in Step 4.
        """
        keep = self.chk_mc_keep.isChecked()
        for job in self._mc_jobs:
            base = job['base']
            if not keep:
                cleanup_mc_spectra(job)
                self.txt_log.append(f"🧹 Monte Carlo {base}: perturbed spectra removed ({job['spec_dir']})")
            done = [o for o in job['outs'] if os.path.exists(o)]
            if len(done) < 2:
                self.txt_log.append(f"⚠️ Monte Carlo {base}: only {len(done)} fit(s) produced — no statistics.")
                continue
            try:
                mc = load_mc_outputs(done)
                stats = mc_statistics(mc, self.pylight_config, self.sb_gal_dist.value())
                table = os.path.join(job['root'], f"{base}_mc_props.csv")
                write_mc_table(stats, table, name=base, pylight_config=self.pylight_config)
                self.txt_log.append(f"📊 Monte Carlo {base}: mean ± std of {mc['n']} fits → {table}")
                self.load_mc_set(done)
                plot = os.path.join(job['root'], f"{base}_mc.png")
                self.fig_results.savefig(plot, dpi=200, bbox_inches='tight')
                self.txt_log.append(f"🖼️ Monte Carlo {base}: plot (mean ± std) → {plot}")
            except Exception as e:
                self.txt_log.append(f"❌ Monte Carlo {base}: {e}")
        self._mc_jobs = []

    def _on_stop_starlight_clicked(self):
        if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
            self.txt_log.append("🛑 Requesting execution cancellation...")
            self.worker_thread.cancel()
            self.btn_stop_starlight.setEnabled(False)

    def _on_grid_finished(self, result):
        val = self.progress_bar.value() + 1
        self.progress_bar.setValue(val)

    def _on_all_starlight_finished(self):
        self.btn_run_starlight.setEnabled(True)
        self.btn_stop_starlight.setEnabled(False)
        self.txt_log.append("STARLIGHT batch completed.")
        if getattr(self, '_mc_jobs', None):
            self._finish_mc()
        self.statusBar().showMessage("STARLIGHT batch finished.")
        QMessageBox.information(self, "Finished", "STARLIGHT run finished! Check Results tab to analyze fits.")
