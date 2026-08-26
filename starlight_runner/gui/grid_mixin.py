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

from ..runner import StarlightConfig, generate_grid_files
from ..custom_widgets import StarlightWorkerThread

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

        # Base Manifest File with Browse button
        row_base_file = QHBoxLayout()
        self.txt_base_file = QLineEdit(self.starlight_config.base_file)
        btn_browse_base_file = QPushButton("...")
        btn_browse_base_file.setFixedWidth(36)
        btn_browse_base_file.setToolTip("Select Base Manifest File (e.g. BasesXSLKrupaPCRR, BaseHRpyPopStarChab)")
        btn_browse_base_file.clicked.connect(self._on_browse_base_file)
        row_base_file.addWidget(self.txt_base_file)
        row_base_file.addWidget(btn_browse_base_file)
        f_paths.addRow("Base Manifest File:", row_base_file)

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
        f, _ = QFileDialog.getOpenFileName(self, "Select STARLIGHT Mask File", self.txt_mask_file.text(), "All Files (*);;Starlight Mask (*.mask)")
        if f:
            rel = os.path.basename(f) if os.path.dirname(os.path.abspath(f)) == os.getcwd() else self._to_relpath(f)
            self.txt_mask_file.setText(rel)
            self.starlight_config.mask_file = rel

    def _on_browse_config_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Configuration File (.config)", self.txt_config_file.text(), "All Files (*);;Config Files (*.config)")
        if f:
            rel = os.path.basename(f)
            self.txt_config_file.setText(rel)
            self.starlight_config.config_file = rel

    def _on_browse_base_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Base Populations Directory", self.txt_base_dir.text())
        if d:
            rel = self._to_relpath(d)
            self.txt_base_dir.setText(rel)
            self.starlight_config.base_dir = rel

    def _on_browse_base_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Base Manifest File (e.g. BasesXSLKrupaPCRR, BaseHRpyPopStarChab)", self.txt_base_file.text(), "All Files (*)")
        if f:
            rel = os.path.basename(f)
            self.txt_base_file.setText(rel)
            self.starlight_config.base_file = rel

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
        self.starlight_config.llow_sn = self.spin_sn_low.value()
        self.starlight_config.lupp_sn = self.spin_sn_upp.value()
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
            grids = generate_grid_files(spec_files, self.starlight_config)
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
            cwd=".",
            max_workers=self.starlight_config.procs
        )
        self.worker_thread.grid_finished.connect(self._on_grid_finished)
        self.worker_thread.log_message.connect(self.txt_log.append)
        self.worker_thread.all_finished.connect(self._on_all_starlight_finished)

        self.btn_run_starlight.setEnabled(False)
        self.btn_stop_starlight.setEnabled(True)
        self.worker_thread.start()

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
        self.statusBar().showMessage("STARLIGHT batch finished.")
        QMessageBox.information(self, "Finished", "STARLIGHT run finished! Check Results tab to analyze fits.")
