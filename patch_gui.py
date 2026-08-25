import re

file_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace "Executar STARLIGHT"
content = content.replace('"Executar STARLIGHT"', '"Run STARLIGHT"')

# Replace the layout in _create_step3_runner
old_layout = """        # Action Buttons
        btn_generate_grids = QPushButton("Generate Grid Files (grid_*.inp)")
        btn_generate_grids.clicked.connect(self._on_generate_grids)
        left_layout.addWidget(btn_generate_grids)

        self.btn_run_starlight = QPushButton("Run STARLIGHT")
        self.btn_run_starlight.setStyleSheet("background-color: #10B981; color: white; font-size: 14px;")
        self.btn_run_starlight.clicked.connect(self._on_run_starlight_clicked)
        left_layout.addWidget(self.btn_run_starlight)"""

new_layout = """        # Action Buttons
        row_cfg_btns = QHBoxLayout()
        btn_load_cfg = QPushButton("Load Config State")
        btn_load_cfg.clicked.connect(self._on_load_config_state)
        btn_save_cfg = QPushButton("Save Config State")
        btn_save_cfg.clicked.connect(self._on_save_config_state)
        row_cfg_btns.addWidget(btn_load_cfg)
        row_cfg_btns.addWidget(btn_save_cfg)
        left_layout.addLayout(row_cfg_btns)

        btn_generate_grids = QPushButton("Generate Grid Files (grid_*.inp)")
        btn_generate_grids.clicked.connect(self._on_generate_grids)
        left_layout.addWidget(btn_generate_grids)

        self.btn_run_starlight = QPushButton("Run STARLIGHT")
        self.btn_run_starlight.setStyleSheet("background-color: #10B981; color: white; font-size: 14px;")
        self.btn_run_starlight.clicked.connect(self._on_run_starlight_clicked)
        left_layout.addWidget(self.btn_run_starlight)"""

content = content.replace(old_layout, new_layout)

# Inject the methods before _on_generate_grids
methods_str = """
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
                    "mask_file": self.txt_mask_file.text(),
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
                self.txt_mask_file.setText(state.get("mask_file", ""))
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

    def _on_generate_grids(self):"""

content = content.replace("    def _on_generate_grids(self):", methods_str)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied successfully!")
