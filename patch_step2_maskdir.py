import re

gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

# 1. Update the numbering of groups in Step 2
gcontent = gcontent.replace('QGroupBox("1. Modo Interativo (CreateMasks)")', 'QGroupBox("2. Modo Interativo (CreateMasks)")')
gcontent = gcontent.replace('QGroupBox("2. Mask Presets")', 'QGroupBox("3. Mask Presets")')
gcontent = gcontent.replace('QGroupBox("3. Add Mask Region Manualmente")', 'QGroupBox("4. Add Mask Region Manualmente")')
gcontent = gcontent.replace('QGroupBox("4. Spectral Mask (List)")', 'QGroupBox("5. Spectral Mask (List)")')

# 2. Inject 1. Masks Directory after 0. Target Spectrum
target_spec_block = """        self.lbl_mask_loaded_file.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        f_spec.addWidget(btn_load_spec_mask)
        f_spec.addWidget(self.lbl_mask_loaded_file)
        left_layout.addWidget(grp_spec)"""

mask_dir_block = """        self.lbl_mask_loaded_file.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
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
        left_layout.addWidget(grp_mdir)"""

gcontent = gcontent.replace(target_spec_block, mask_dir_block)

# 3. Change default mask_ext to .mask
gcontent = gcontent.replace('mask_ext = mask_ext.mask_ext if mask_ext else ".sm"', 'mask_ext = mask_ext.mask_ext if mask_ext else ".mask"')
gcontent = gcontent.replace('self.txt_mask_ext.setPlaceholderText(".sm")', 'self.txt_mask_ext.setPlaceholderText(".mask")')
gcontent = gcontent.replace('state.get("mask_ext", ".sm")', 'state.get("mask_ext", ".mask")')
gcontent = gcontent.replace('self.starlight_config.mask_ext\n', 'self.starlight_config.mask_ext or ".mask"\n') # safety
gcontent = gcontent.replace('default_name = "mask.sm"', 'default_name = "mask.mask"')

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

print("Step 2 UI patched.")
