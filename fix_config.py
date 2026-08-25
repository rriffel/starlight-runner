import re
import json

gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

# 1. Update _on_save_config_state
old_save = """    def _on_save_config_state(self):
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
                    "procs": self.spin_procs.value()
                }
                with open(filepath, 'w') as f:
                    json.dump(state, f, indent=4)
                QMessageBox.information(self, "Config Saved", f"Configuration state saved to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save config: {e}")"""

new_save = """    def _on_save_config_state(self):
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
                QMessageBox.critical(self, "Error", f"Could not save config: {e}")"""

# 2. Update _on_load_config_state
old_load = """    def _on_load_config_state(self):
        import json
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration State", "", "JSON Files (*.json);;All Files (*)"
        )
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    state = json.load(f)
                
                self.txt_exe.setText(state.get("exe", "StarlightChains_v04.exe"))
                self.txt_obs_dir.setText(state.get("obs_dir", ""))
                self.combo_spec_ext.setCurrentText(state.get("spec_ext", ".spec"))
                
                mdir = state.get("mask_dir", "")
                if hasattr(self, 'txt_mask_dir_step3'):
                    self.txt_mask_dir_step3.setText(mdir)
                if hasattr(self, 'txt_mask_dir_step2'):
                    self.txt_mask_dir_step2.setText(mdir)
                    
                self.txt_mask_ext.setText(state.get("mask_ext", ".mask"))
                self.txt_config_file.setText(state.get("config_file", ""))
                self.txt_base_dir.setText(state.get("base_dir", ""))
                self.txt_base_file.setText(state.get("base_file", ""))
                self.txt_out_dir.setText(state.get("out_dir", ""))
                self.spin_fit_ini.setValue(state.get("fit_ini", 3400.0))
                self.spin_fit_fin.setValue(state.get("fit_fin", 8900.0))
                self.spin_sn_low.setValue(state.get("sn_low", 4010.0))
                self.spin_sn_upp.setValue(state.get("sn_upp", 4060.0))
                self.combo_kinematics.setCurrentText(state.get("kinematics", "1"))
                self.spin_procs.setValue(state.get("procs", 4))
                
                self._sync_config_from_ui()
                QMessageBox.information(self, "Config Loaded", f"Configuration loaded from {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load config: {e}")"""

new_load = """    def _on_load_config_state(self):
        import json
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration State", "", "JSON Files (*.json);;All Files (*)"
        )
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    state = json.load(f)
                
                self.txt_exe.setText(state.get("exe", "StarlightChains_v04.exe"))
                self.txt_obs_dir.setText(state.get("obs_dir", ""))
                self.combo_spec_ext.setCurrentText(state.get("spec_ext", ".spec"))
                
                mdir = state.get("mask_dir", "")
                if hasattr(self, 'txt_mask_dir_step3'):
                    self.txt_mask_dir_step3.setText(mdir)
                if hasattr(self, 'txt_mask_dir_step2'):
                    self.txt_mask_dir_step2.setText(mdir)
                    
                self.txt_mask_ext.setText(state.get("mask_ext", ".mask"))
                self.txt_config_file.setText(state.get("config_file", ""))
                self.txt_base_dir.setText(state.get("base_dir", ""))
                self.txt_base_file.setText(state.get("base_file", ""))
                self.txt_out_dir.setText(state.get("out_dir", ""))
                self.spin_fit_ini.setValue(state.get("fit_ini", 3400.0))
                self.spin_fit_fin.setValue(state.get("fit_fin", 8900.0))
                self.spin_sn_low.setValue(state.get("sn_low", 4010.0))
                self.spin_sn_upp.setValue(state.get("sn_upp", 4060.0))
                self.combo_kinematics.setCurrentText(state.get("kinematics", "1"))
                self.spin_procs.setValue(state.get("procs", 4))

                if "z" in state: self.spin_z.setValue(state.get("z", 0.0))
                if "law" in state: self.combo_law.setCurrentText(state.get("law", "ccm"))
                if "av" in state: self.spin_av.setValue(state.get("av", 0.0))
                if "rv" in state: self.spin_rv.setValue(state.get("rv", 3.1))
                if "rebin_step" in state: self.spin_rebin_step.setValue(state.get("rebin_step", 1.0))
                
                self._sync_config_from_ui()
                QMessageBox.information(self, "Config Loaded", f"Configuration loaded from {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load config: {e}")"""

gcontent = gcontent.replace(old_save, new_save)
gcontent = gcontent.replace(old_load, new_load)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

