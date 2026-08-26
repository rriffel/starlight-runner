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

from ..masking import SpectralMask

class ConfigMixin:
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
                    "is_err_available": 1 if self.chk_err_spec.isChecked() else 0,
                    "is_flag_available": 1 if self.chk_flag_spec.isChecked() else 0,
                    "seed": self.spin_seed.value(),
                    "z": self.spin_z.value(),
                    "law": self.combo_law.currentText(),
                    "av": self.spin_av.value(),
                    "rv": self.spin_rv.value(),
                    "rebin_step": self.spin_rebin_step.value(),
                    "telluric_cuts": getattr(self, 'telluric_cuts', []),
                    "trim_bounds_enabled": self.chk_trim_bounds.isChecked(),
                    "trim_min": self.spin_trim_min.value(),
                    "trim_max": self.spin_trim_max.value(),
                    "masks": getattr(self.spectral_mask, 'intervals', []),
                    "pylight_config": getattr(self, 'pylight_config', {})
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
                if "is_err_available" in state: self.chk_err_spec.setChecked(bool(state["is_err_available"]))
                if "is_flag_available" in state: self.chk_flag_spec.setChecked(bool(state["is_flag_available"]))
                if "seed" in state: self.spin_seed.setValue(state["seed"])
                
                if "z" in state: self.spin_z.setValue(state["z"])
                if "law" in state: self.combo_law.setCurrentText(state["law"])
                if "av" in state: self.spin_av.setValue(state["av"])
                if "rv" in state: self.spin_rv.setValue(state["rv"])
                if "rebin_step" in state: self.spin_rebin_step.setValue(state["rebin_step"])
                
                # Restore telluric cuts (backward compat: fall back to "cuts" key)
                saved_cuts = state.get("telluric_cuts", state.get("cuts", []))
                if saved_cuts:
                    self.telluric_cuts = saved_cuts
                    if hasattr(self, '_update_cuts_table'): self._update_cuts_table()
                    if hasattr(self, '_plot_preprocessing'): self._plot_preprocessing()

                # Restore spectrum edge trimming bounds
                if "trim_bounds_enabled" in state:
                    self.chk_trim_bounds.setChecked(state["trim_bounds_enabled"])
                if "trim_min" in state:
                    self.spin_trim_min.setValue(state["trim_min"])
                if "trim_max" in state:
                    self.spin_trim_max.setValue(state["trim_max"])
                    
                if "masks" in state:
                    self.spectral_mask.intervals = state["masks"]
                    if hasattr(self, '_update_mask_table'): self._update_mask_table()
                    if hasattr(self, '_plot_masking'): self._plot_masking()
                    
                if "pylight_config" in state:
                    self.pylight_config = state["pylight_config"]
                    if hasattr(self, '_plot_results'): self._plot_results()
                
                self._sync_config_from_ui()
                self.statusBar().showMessage(f"Config loaded from {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load config: {e}")
