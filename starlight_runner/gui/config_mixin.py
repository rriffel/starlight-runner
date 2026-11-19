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

from . import constants

from ..masking import SpectralMask

class ConfigMixin:
    def _collect_state(self):
        """Current GUI configuration as a state dict (Save Config State / Export Script)."""
        self._sync_config_from_ui()
        state = {
                    "exe": self.txt_exe.text(),
                    "obs_dir": self.txt_obs_dir.text(),
                    "spec_ext": self.combo_spec_ext.currentText(),
                    "mask_dir": self.txt_mask_dir_step3.text() if hasattr(self, 'txt_mask_dir_step3') else "",
                    "mask_ext": self.txt_mask_ext.text(),
                    "std_mask_enabled": self.chk_std_mask.isChecked() if hasattr(self, 'chk_std_mask') else False,
                    "std_mask_file": self.txt_std_mask.text() if hasattr(self, 'txt_std_mask') else "",
                    "config_file": self.txt_config_file.text(),
                    "base_dir": self.txt_base_dir.text(),
                    "base_file": self.txt_base_file.text(),
                    "out_dir": self.txt_out_dir.text(),
                    "fit_ini": self.spin_fit_ini.value(),
                    "fit_fin": self.spin_fit_fin.value(),
                    # S/N window = normalization window (kept as sn_* for older readers)
                    "sn_low": self.spin_llow_norm.value(),
                    "sn_upp": self.spin_lupp_norm.value(),
                    "l_norm": self.spin_l_norm.value() if hasattr(self, 'spin_l_norm') else None,
                    "llow_norm": self.spin_llow_norm.value() if hasattr(self, 'spin_llow_norm') else None,
                    "lupp_norm": self.spin_lupp_norm.value() if hasattr(self, 'spin_lupp_norm') else None,
                    "kinematics": self.combo_kinematics.currentText(),
                    "procs": self.spin_procs.value(),
                    "is_err_available": 1 if self.chk_err_spec.isChecked() else 0,
                    "is_flag_available": 1 if self.chk_flag_spec.isChecked() else 0,
                    "seed": self.spin_seed.value(),
                    "mc_enabled": self.chk_mc.isChecked(),
                    "mc_n": self.spin_mc_n.value(),
                    "mc_dir": self.txt_mc_dir.text(),
                    "mc_keep_spectra": self.chk_mc_keep.isChecked(),
                    "downgrade_res_enabled": self.chk_downgrade_res.isChecked() if hasattr(self, 'chk_downgrade_res') else False,
                    "res_mode": self.combo_res_mode.currentIndex() if hasattr(self, 'combo_res_mode') else 0,
                    "res_ini_is_file": self.rad_res_ini_file.isChecked() if hasattr(self, 'rad_res_ini_file') else False,
                    "res_ini_file_path": getattr(self, "res_ini_file_path", ""),
                    "res_ini": self.spin_res_ini.value() if hasattr(self, 'spin_res_ini') else 5000.0,
                    "res_tgt_is_file": self.rad_res_tgt_file.isChecked() if hasattr(self, 'rad_res_tgt_file') else False,
                    "res_tgt_file_path": getattr(self, "res_tgt_file_path", ""),
                    "res_tgt": self.spin_res_tgt.value() if hasattr(self, 'spin_res_tgt') else 2000.0,
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
                    "pylight_config": getattr(self, 'pylight_config', {}),
                    "gal_dist": self.sb_gal_dist.value() if hasattr(self, 'sb_gal_dist') else 0.0,
            # run scripts only: apply Step 1 to every spectrum before the fit (no GUI widget)
            "preprocessing_apply": getattr(self, '_preprocessing_apply', False),
            # files open in the GUI, reopened when the config / script is loaded
            "loaded_files": self._loaded_files(),
                }
        return state

    def _on_save_config_state(self):
        import json
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration State", "starlight_gui_config.json", "JSON Files (*.json);;All Files (*)"
        )
        if filepath:
            try:
                state = self._collect_state()
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
                self._apply_state(state)
                self.statusBar().showMessage(f"Config loaded from {filepath}" + getattr(self, '_reopened_msg', ""))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load config: {e}")

    def _apply_state(self, state):
        """Fill the GUI from a state dict (Load Config State / Load Script)."""
        self.txt_exe.setText(state.get("exe", ""))
        self.txt_obs_dir.setText(state.get("obs_dir", ""))
        self.combo_spec_ext.setCurrentText(state.get("spec_ext", "*.spec"))
        if hasattr(self, 'txt_mask_dir_step3'): self.txt_mask_dir_step3.setText(state.get("mask_dir", ""))
        self.txt_mask_ext.setText(state.get("mask_ext", ".mask"))
        if hasattr(self, 'chk_std_mask'):
            self.txt_std_mask.setText(state.get("std_mask_file", ""))
            enabled = bool(state.get("std_mask_enabled", False)) and bool(self.txt_std_mask.text().strip())
            self.chk_std_mask.blockSignals(True)
            self.chk_std_mask.setChecked(enabled)
            self.chk_std_mask.blockSignals(False)
            self._on_toggle_std_mask(enabled)
        self.txt_config_file.setText(state.get("config_file", ""))
        self.txt_base_dir.setText(state.get("base_dir", ""))
        self.txt_base_file.setText(state.get("base_file", ""))
        self.txt_out_dir.setText(state.get("out_dir", ""))
        
        if "fit_ini" in state: self.spin_fit_ini.setValue(state["fit_ini"])
        if "fit_fin" in state: self.spin_fit_fin.setValue(state["fit_fin"])
        if hasattr(self, 'spin_l_norm'):
            self._sync_norm_from_config_file()  # window of the loaded .config ...
            # ... unless the state saved its own window (older states: S/N window)
            for keys, w in ((("llow_norm", "sn_low"), self.spin_llow_norm),
                            (("lupp_norm", "sn_upp"), self.spin_lupp_norm)):
                val = next((state[k] for k in keys if state.get(k) is not None), None)
                if val is not None:
                    w.setValue(val)
            self._update_l_norm()  # l_norm = mean of the window
        if "kinematics" in state: self.combo_kinematics.setCurrentText(state["kinematics"])
        if "procs" in state: self.spin_procs.setValue(state["procs"])
        if "is_err_available" in state: self.chk_err_spec.setChecked(bool(state["is_err_available"]))
        if "is_flag_available" in state: self.chk_flag_spec.setChecked(bool(state["is_flag_available"]))
        if "seed" in state: self.spin_seed.setValue(state["seed"])
        if "mc_n" in state: self.spin_mc_n.setValue(state["mc_n"])
        if "mc_dir" in state: self.txt_mc_dir.setText(state["mc_dir"])
        if "mc_keep_spectra" in state: self.chk_mc_keep.setChecked(bool(state["mc_keep_spectra"]))
        if "mc_enabled" in state: self.chk_mc.setChecked(bool(state["mc_enabled"]))
        
        if hasattr(self, 'chk_downgrade_res') and "downgrade_res_enabled" in state:
            self.chk_downgrade_res.setChecked(bool(state["downgrade_res_enabled"]))
        if hasattr(self, 'combo_res_mode') and "res_mode" in state:
            self.combo_res_mode.setCurrentIndex(int(state["res_mode"]))
        
        if hasattr(self, 'rad_res_ini_file') and "res_ini_is_file" in state:
            if state["res_ini_is_file"]:
                self.rad_res_ini_file.setChecked(True)
            else:
                self.rad_res_ini_const.setChecked(True)
        if "res_ini_file_path" in state and state["res_ini_file_path"]:
            self.res_ini_file_path = state["res_ini_file_path"]
            if hasattr(self, 'lbl_res_ini_file'):
                self.lbl_res_ini_file.setText(f"Vector: {os.path.basename(self.res_ini_file_path)}")

        if hasattr(self, 'rad_res_tgt_file') and "res_tgt_is_file" in state:
            if state["res_tgt_is_file"]:
                self.rad_res_tgt_file.setChecked(True)
            else:
                self.rad_res_tgt_const.setChecked(True)
        if "res_tgt_file_path" in state and state["res_tgt_file_path"]:
            self.res_tgt_file_path = state["res_tgt_file_path"]
            if hasattr(self, 'lbl_res_tgt_file'):
                self.lbl_res_tgt_file.setText(f"Vector: {os.path.basename(self.res_tgt_file_path)}")

        if hasattr(self, 'spin_res_ini') and "res_ini" in state:
            self.spin_res_ini.setValue(float(state["res_ini"]))
        if hasattr(self, 'spin_res_tgt') and "res_tgt" in state:
            self.spin_res_tgt.setValue(float(state["res_tgt"]))

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
            from ..pylight_reader import migrate_fc_bins
            if migrate_fc_bins(self.pylight_config):
                self.statusBar().showMessage(
                    "PyLight FC bins converted to the agn_fc_<alpha> nomenclature (FC0.25/0.50/0.75).", 8000)
        if hasattr(self, '_sync_pylight_zs'):
            self._sync_pylight_zs()  # Zs always from the Base File
        self._preprocessing_apply = bool(state.get("preprocessing_apply", False))
        if "gal_dist" in state and hasattr(self, 'sb_gal_dist'):
            self.sb_gal_dist.setValue(float(state["gal_dist"]))
        if "pylight_config" in state and hasattr(self, '_plot_results'):
            self._plot_results()

        self._sync_config_from_ui()
        self._reopen_files(state.get("loaded_files") or {})

    def _loaded_files(self):
        """Spectra / fits open in Steps 1, 2 and 4 (paths relative to the GUI folder)."""
        rel = self._to_relpath if hasattr(self, '_to_relpath') else (lambda p: p)
        step1 = getattr(self, 'step1_spectrum_path', None)
        step2 = getattr(self, 'masking_spectrum_path', None)
        return {
            "step1": rel(step1) if step1 else None,
            "step1_processed": bool(step1) and bool(getattr(self, '_step1_processed', False)),
            "step2": rel(step2) if step2 else None,
            "results": [rel(f) for f in getattr(self, 'results_files', []) or []],
        }

    def _reopen_files(self, files):
        """Reopen the spectra / fits recorded in a config or script (after its parameters are set)."""
        missing, opened = [], []
        step1, step2 = files.get("step1"), files.get("step2")
        if step1:
            if os.path.isfile(step1):
                self.load_spectrum_file(step1)
                if files.get("step1_processed"):
                    if self._run_preprocessing_internal(silent=True):
                        self._preproc_done = self._step1_processed = True
                        self._plot_preprocessing()
                opened.append(f"Step 1: {os.path.basename(step1)}")
            else:
                missing.append(step1)
        if step2:
            if os.path.isfile(step2):
                self.load_spectrum_for_masking(step2)
                opened.append(f"Step 2: {os.path.basename(step2)}")
            else:
                missing.append(step2)
        results = files.get("results") or []
        found = [f for f in results if os.path.isfile(f)]
        missing += [f for f in results if not os.path.isfile(f)]
        if len(found) == 1:
            self.load_starlight_out(found[0])
        elif len(found) > 1:
            self.load_mc_set(found)
        if found:
            opened.append(f"Step 4: {len(found)} fit(s)")
        self._reopened_msg = ("  —  reopened " + "; ".join(opened)) if opened else ""
        if missing:
            QMessageBox.warning(self, "Files Not Found",
                                "These files saved with the configuration were not found:\n\n"
                                + "\n".join(missing))

    def _on_export_script(self):
        """Write the current Step 3 / PyLight configuration as a standalone run script (.py)."""
        from ..scripting import generate_script, workdir_for_script
        path, _ = QFileDialog.getSaveFileName(
            self, "Export STARLIGHT Runner Script", "run_starlight.py", "Python Files (*.py);;All Files (*)"
        )
        if not path:
            return
        try:
            # paths in the state are relative to the GUI's folder: the script
            # finds that folder relative to its own location
            rel = workdir_for_script(path, os.getcwd())
            with open(path, "w") as fh:
                fh.write(generate_script(self._collect_state(), workdir_rel=rel))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not write script: {e}")
            return
        self.statusBar().showMessage(f"Script exported to {path}")
        QMessageBox.information(
            self, "Script Exported",
            f"Script written to:\n{path}\n\nRun it with:\n   python {os.path.basename(path)}\n\n"
            "It can be loaded back with 'Load Script (.py)'."
        )

    def _on_load_script(self):
        """Fill the GUI from a run script (inverse of Export Script). Runs the script's code."""
        from ..scripting import import_script, ScriptImportError
        if getattr(self, 'worker_thread', None) is not None and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Running", "Wait for the current STARLIGHT run to finish first.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Load STARLIGHT Runner Script", "", "Python Files (*.py);;All Files (*)"
        )
        if not path:
            return
        reply = QMessageBox.question(
            self, "Load Script",
            "This runs the script's own code to read its configuration (STARLIGHT itself is not run) — "
            f"the same as running it yourself. Only continue if you trust '{os.path.basename(path)}'.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            state, warnings = import_script(path, gui_cwd=os.getcwd())
        except ScriptImportError as e:
            QMessageBox.critical(self, "Could Not Load Script", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Could Not Load Script", f"Unexpected error: {e}")
            return
        self._apply_state(state)
        self.statusBar().showMessage(f"Configuration imported from {path}" + getattr(self, '_reopened_msg', ""))
        if warnings:
            QMessageBox.warning(self, "Imported With Warnings",
                                "The script's configuration was imported, but:\n\n"
                                + "\n\n".join(f"• {w}" for w in warnings))
        else:
            QMessageBox.information(self, "Script Loaded", f"Configuration imported from:\n{path}")
