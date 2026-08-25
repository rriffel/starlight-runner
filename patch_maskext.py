import re

runner_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/runner.py"
with open(runner_path, "r", encoding="utf-8") as f:
    rcontent = f.read()

rcontent = rcontent.replace('self.mask_file = kwargs.get("mask_file", "")', 'self.mask_ext = kwargs.get("mask_ext", ".sm")')

old_mask_logic = """                # Automatic mask resolution: look for <spec_base>.sm matching this spectrum
                dedicated_mask = f"{base_name}.sm"
                if spec_dir and os.path.exists(os.path.join(spec_dir, dedicated_mask)):
                    mask_name = dedicated_mask
                elif config.obs_dir and os.path.exists(os.path.join(config.obs_dir, dedicated_mask)):
                    mask_name = dedicated_mask
                elif config.mask_dir and os.path.exists(os.path.join(config.mask_dir, dedicated_mask)):
                    mask_name = dedicated_mask
                elif os.path.exists(dedicated_mask):
                    mask_name = dedicated_mask
                elif os.path.exists(f"mask_{base_name}.sm"):
                    mask_name = f"mask_{base_name}.sm"
                else:
                    # Fallback to configured mask_file or default_mask_file
                    mask_name = os.path.basename(default_mask_file) if default_mask_file else (
                        os.path.basename(config.mask_file) if config.mask_file else "mask.sm"
                    )"""

new_mask_logic = """                mask_ext = config.mask_ext if config.mask_ext.startswith('.') else f".{config.mask_ext}"
                mask_name = f"{base_name}{mask_ext}\""""

rcontent = rcontent.replace(old_mask_logic, new_mask_logic)
with open(runner_path, "w", encoding="utf-8") as f:
    f.write(rcontent)


gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

# Remove txt_mask_file, add txt_mask_ext
old_mask_ui = """        # Mask File with Browse button
        row_mask = QHBoxLayout()
        self.txt_mask_file = QLineEdit(self.starlight_config.mask_file)
        btn_browse_mask = QPushButton("...")
        btn_browse_mask.setFixedWidth(36)
        btn_browse_mask.setToolTip("Open Mask File (.sm)")
        btn_browse_mask.clicked.connect(self._on_browse_mask_file)
        row_mask.addWidget(self.txt_mask_file)
        row_mask.addWidget(btn_browse_mask)
        f_paths.addRow("Default Mask (Optional):", row_mask)"""

new_mask_ui = """        # Mask Extension
        self.txt_mask_ext = QLineEdit(self.starlight_config.mask_ext)
        self.txt_mask_ext.setPlaceholderText(".sm")
        f_paths.addRow("Mask Extension:", self.txt_mask_ext)"""
gcontent = gcontent.replace(old_mask_ui, new_mask_ui)

# Fix InteractiveMaskDialog default save path
old_save_deriv = """        if self.spectrum_path:
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
new_save_deriv = """        mask_ext = getattr(parent, 'starlight_config', None)
        mask_ext = mask_ext.mask_ext if mask_ext else ".sm"
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
                self.default_mask_path = f"mask{mask_ext}\""""
gcontent = gcontent.replace(old_save_deriv, new_save_deriv)

# Fix _on_save_sm_dialog
old_save_sm = """        mask_dir = self.txt_mask_dir_step2.text().strip() if hasattr(self, 'txt_mask_dir_step2') else None
        if spec_path:
            spec_base = os.path.splitext(os.path.basename(spec_path))[0]
            if mask_dir:
                default_name = os.path.join(mask_dir, f"{spec_base}.sm")
            else:
                spec_dir = os.path.dirname(spec_path)
                default_name = os.path.join(spec_dir, f"{spec_base}.sm") if spec_dir else f"{spec_base}.sm\""""
new_save_sm = """        mask_dir = self.txt_mask_dir_step2.text().strip() if hasattr(self, 'txt_mask_dir_step2') else None
        mask_ext = self.starlight_config.mask_ext
        if not mask_ext.startswith('.'): mask_ext = "." + mask_ext
        if spec_path:
            spec_base = os.path.splitext(os.path.basename(spec_path))[0]
            if mask_dir:
                default_name = os.path.join(mask_dir, f"{spec_base}{mask_ext}")
            else:
                spec_dir = os.path.dirname(spec_path)
                default_name = os.path.join(spec_dir, f"{spec_base}{mask_ext}") if spec_dir else f"{spec_base}{mask_ext}\""""
gcontent = gcontent.replace(old_save_sm, new_save_sm)

# Replace config save/load
old_save_cfg = """                    "mask_dir": self.txt_mask_dir_step3.text() if hasattr(self, 'txt_mask_dir_step3') else "",
                    "mask_file": self.txt_mask_file.text(),
                    "config_file": self.txt_config_file.text(),"""
new_save_cfg = """                    "mask_dir": self.txt_mask_dir_step3.text() if hasattr(self, 'txt_mask_dir_step3') else "",
                    "mask_ext": self.txt_mask_ext.text(),
                    "config_file": self.txt_config_file.text(),"""
gcontent = gcontent.replace(old_save_cfg, new_save_cfg)

old_load_cfg = """                if hasattr(self, 'txt_mask_dir_step3'): self.txt_mask_dir_step3.setText(state.get("mask_dir", ""))
                self.txt_mask_file.setText(state.get("mask_file", ""))
                self.txt_config_file.setText(state.get("config_file", ""))"""
new_load_cfg = """                if hasattr(self, 'txt_mask_dir_step3'): self.txt_mask_dir_step3.setText(state.get("mask_dir", ""))
                self.txt_mask_ext.setText(state.get("mask_ext", ".sm"))
                self.txt_config_file.setText(state.get("config_file", ""))"""
gcontent = gcontent.replace(old_load_cfg, new_load_cfg)

# Sync config from UI
old_sync = """        self.starlight_config.mask_file = self.txt_mask_file.text().strip()"""
new_sync = """        self.starlight_config.mask_ext = self.txt_mask_ext.text().strip()"""
gcontent = gcontent.replace(old_sync, new_sync)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

print("Patch mask ext applied!")
