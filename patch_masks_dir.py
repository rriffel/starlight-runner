import re

file_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update InteractiveMaskDialog __init__ to accept mask_dir
# -----------------------------------------------------------
old_init = """    def __init__(self, parent, wl, flux, eflux, spectral_mask, spectrum_path=None):"""
new_init = """    def __init__(self, parent, wl, flux, eflux, spectral_mask, spectrum_path=None, mask_dir=None):"""
content = content.replace(old_init, new_init)

old_deriv = """        # Derive default mask filename: <spec_base>.sm
        if self.spectrum_path:
            spec_dir = os.path.dirname(self.spectrum_path)
            spec_base = os.path.splitext(os.path.basename(self.spectrum_path))[0]
            self.default_mask_path = os.path.join(spec_dir, f"{spec_base}.sm") if spec_dir else f"{spec_base}.sm"
        else:
            self.default_mask_path = "mask.sm\""""
new_deriv = """        # Derive default mask filename: <spec_base>.sm
        if self.spectrum_path:
            spec_base = os.path.splitext(os.path.basename(self.spectrum_path))[0]
            if mask_dir:
                self.default_mask_path = os.path.join(mask_dir, f"{spec_base}.sm")
            else:
                spec_dir = os.path.dirname(self.spectrum_path)
                self.default_mask_path = os.path.join(spec_dir, f"{spec_base}.sm") if spec_dir else f"{spec_base}.sm"
        else:
            if mask_dir:
                self.default_mask_path = os.path.join(mask_dir, "mask.sm")
            else:
                self.default_mask_path = "mask.sm\""""
content = content.replace(old_deriv, new_deriv)

# 2. Update _on_open_detached_mask_dialog in MainWindow
# -----------------------------------------------------
old_open_dlg = """        spec_path = getattr(self, 'current_spectrum_path', None)
        dlg = InteractiveMaskDialog(self, wl, flx, eflx, self.spectral_mask, spectrum_path=spec_path)"""
new_open_dlg = """        spec_path = getattr(self, 'current_spectrum_path', None)
        mask_dir = self.txt_mask_dir_step2.text().strip() if hasattr(self, 'txt_mask_dir_step2') else None
        dlg = InteractiveMaskDialog(self, wl, flx, eflx, self.spectral_mask, spectrum_path=spec_path, mask_dir=mask_dir)"""
content = content.replace(old_open_dlg, new_open_dlg)

# 3. Update _on_save_sm_dialog
# ----------------------------
old_save_dlg = """    def _on_save_sm_dialog(self):
        default_name = "mask.sm"
        spec_path = getattr(self, 'current_spectrum_path', None)
        if spec_path:
            spec_dir = os.path.dirname(spec_path)
            spec_base = os.path.splitext(os.path.basename(spec_path))[0]
            default_name = os.path.join(spec_dir, f"{spec_base}.sm") if spec_dir else f"{spec_base}.sm\""""
new_save_dlg = """    def _on_save_sm_dialog(self):
        default_name = "mask.sm"
        spec_path = getattr(self, 'current_spectrum_path', None)
        mask_dir = self.txt_mask_dir_step2.text().strip() if hasattr(self, 'txt_mask_dir_step2') else None
        if spec_path:
            spec_base = os.path.splitext(os.path.basename(spec_path))[0]
            if mask_dir:
                default_name = os.path.join(mask_dir, f"{spec_base}.sm")
            else:
                spec_dir = os.path.dirname(spec_path)
                default_name = os.path.join(spec_dir, f"{spec_base}.sm") if spec_dir else f"{spec_base}.sm\""""
content = content.replace(old_save_dlg, new_save_dlg)

# 4. Add "Masks Directory" UI in Step 2 (Masking)
# -----------------------------------------------
old_step2_ui = """        # 0. Target Spectrum Group
        grp_spec = QGroupBox("0. Target Spectrum")
        f_spec = QVBoxLayout(grp_spec)
        btn_load_spec_mask = QPushButton("Load Spectrum...")
        btn_load_spec_mask.clicked.connect(self._on_load_spectrum_for_masking_dialog)
        self.lbl_mask_loaded_file = QLabel("No spectrum loaded (or use from Step 1)")
        self.lbl_mask_loaded_file.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        f_spec.addWidget(btn_load_spec_mask)
        f_spec.addWidget(self.lbl_mask_loaded_file)
        left_layout.addWidget(grp_spec)"""

new_step2_ui = """        # 0. Target Spectrum Group
        grp_spec = QGroupBox("0. Target Spectrum")
        f_spec = QVBoxLayout(grp_spec)
        btn_load_spec_mask = QPushButton("Load Spectrum...")
        btn_load_spec_mask.clicked.connect(self._on_load_spectrum_for_masking_dialog)
        self.lbl_mask_loaded_file = QLabel("No spectrum loaded (or use from Step 1)")
        self.lbl_mask_loaded_file.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        f_spec.addWidget(btn_load_spec_mask)
        f_spec.addWidget(self.lbl_mask_loaded_file)
        left_layout.addWidget(grp_spec)

        # 0.5 Masks Directory
        grp_mask_dir2 = QGroupBox("0.5. Masks Directory (Save Location)")
        f_mask_dir2 = QHBoxLayout(grp_mask_dir2)
        self.txt_mask_dir_step2 = QLineEdit(self.starlight_config.mask_dir)
        self.txt_mask_dir_step2.setPlaceholderText("Directory to save .sm files")
        self.txt_mask_dir_step2.textChanged.connect(self._sync_mask_dirs)
        btn_browse_mdir2 = QPushButton("...")
        btn_browse_mdir2.setFixedWidth(36)
        btn_browse_mdir2.clicked.connect(self._on_browse_mask_dir_step2)
        f_mask_dir2.addWidget(self.txt_mask_dir_step2)
        f_mask_dir2.addWidget(btn_browse_mdir2)
        left_layout.addWidget(grp_mask_dir2)"""

content = content.replace(old_step2_ui, new_step2_ui)


# 5. Add "Masks Directory" UI in Step 3 (Runner)
# -----------------------------------------------
old_step3_ui = """        # Mask File with Browse button
        row_mask = QHBoxLayout()
        self.txt_mask_file = QLineEdit(self.starlight_config.mask_file)
        btn_browse_mask = QPushButton("...")
        btn_browse_mask.setFixedWidth(36)
        btn_browse_mask.setToolTip("Open Mask File (.sm)")
        btn_browse_mask.clicked.connect(self._on_browse_mask_file)
        row_mask.addWidget(self.txt_mask_file)
        row_mask.addWidget(btn_browse_mask)
        f_paths.addRow("Default Mask (Optional):", row_mask)"""

new_step3_ui = """        # Masks Directory with Browse button
        row_mask_dir3 = QHBoxLayout()
        self.txt_mask_dir_step3 = QLineEdit(self.starlight_config.mask_dir)
        self.txt_mask_dir_step3.setPlaceholderText("Folder with .sm files")
        self.txt_mask_dir_step3.textChanged.connect(self._sync_mask_dirs)
        btn_browse_mdir3 = QPushButton("...")
        btn_browse_mdir3.setFixedWidth(36)
        btn_browse_mdir3.clicked.connect(self._on_browse_mask_dir_step3)
        row_mask_dir3.addWidget(self.txt_mask_dir_step3)
        row_mask_dir3.addWidget(btn_browse_mdir3)
        f_paths.addRow("Masks Directory:", row_mask_dir3)

        # Mask File with Browse button
        row_mask = QHBoxLayout()
        self.txt_mask_file = QLineEdit(self.starlight_config.mask_file)
        btn_browse_mask = QPushButton("...")
        btn_browse_mask.setFixedWidth(36)
        btn_browse_mask.setToolTip("Open Mask File (.sm)")
        btn_browse_mask.clicked.connect(self._on_browse_mask_file)
        row_mask.addWidget(self.txt_mask_file)
        row_mask.addWidget(btn_browse_mask)
        f_paths.addRow("Default Mask (Optional):", row_mask)"""

content = content.replace(old_step3_ui, new_step3_ui)

# Add handler methods to MainWindow
handlers = """
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
"""
content = content.replace("    def _on_browse_mask_file(self):", handlers + "\n    def _on_browse_mask_file(self):")


# Update config save/load to include mask_dir
old_save_state = """                    "spec_ext": self.combo_spec_ext.currentText(),
                    "mask_file": self.txt_mask_file.text(),
                    "config_file": self.txt_config_file.text(),"""
new_save_state = """                    "spec_ext": self.combo_spec_ext.currentText(),
                    "mask_dir": self.txt_mask_dir_step3.text() if hasattr(self, 'txt_mask_dir_step3') else "",
                    "mask_file": self.txt_mask_file.text(),
                    "config_file": self.txt_config_file.text(),"""
content = content.replace(old_save_state, new_save_state)

old_load_state = """                self.combo_spec_ext.setCurrentText(state.get("spec_ext", "*.spec"))
                self.txt_mask_file.setText(state.get("mask_file", ""))
                self.txt_config_file.setText(state.get("config_file", ""))"""
new_load_state = """                self.combo_spec_ext.setCurrentText(state.get("spec_ext", "*.spec"))
                if hasattr(self, 'txt_mask_dir_step3'): self.txt_mask_dir_step3.setText(state.get("mask_dir", ""))
                self.txt_mask_file.setText(state.get("mask_file", ""))
                self.txt_config_file.setText(state.get("config_file", ""))"""
content = content.replace(old_load_state, new_load_state)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied for Masks Directory!")
