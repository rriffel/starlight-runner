gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

old_mask_ui = """        # Mask File with Browse button
        row_mask = QHBoxLayout()
        self.txt_mask_file = QLineEdit(self.starlight_config.mask_file)
        btn_browse_mask = QPushButton("...")
        btn_browse_mask.setFixedWidth(36)
        btn_browse_mask.setToolTip("Selecionar Arquivo de Máscara (.sm)")
        btn_browse_mask.clicked.connect(self._on_browse_mask_file)
        row_mask.addWidget(self.txt_mask_file)
        row_mask.addWidget(btn_browse_mask)
        f_paths.addRow("Mask File (.sm):", row_mask)"""

new_mask_ui = """        # Mask Extension
        self.txt_mask_ext = QLineEdit(self.starlight_config.mask_ext)
        self.txt_mask_ext.setPlaceholderText(".sm")
        f_paths.addRow("Mask Extension:", self.txt_mask_ext)"""

gcontent = gcontent.replace(old_mask_ui, new_mask_ui)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

