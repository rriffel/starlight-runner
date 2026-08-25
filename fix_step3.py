import re

gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

old_mask = """        # Mask Extension
        self.txt_mask_ext = QLineEdit(self.starlight_config.mask_ext)
        self.txt_mask_ext.setPlaceholderText(".mask")
        f_paths.addRow("Mask Extension:", self.txt_mask_ext)"""

new_mask = """        # Masks Directory with Browse button
        row_mask_dir = QHBoxLayout()
        self.txt_mask_dir_step3 = QLineEdit(self.starlight_config.mask_dir if hasattr(self.starlight_config, 'mask_dir') else "")
        self.txt_mask_dir_step3.setPlaceholderText("Folder with .mask files")
        btn_browse_mask_dir = QPushButton("...")
        btn_browse_mask_dir.setFixedWidth(36)
        btn_browse_mask_dir.clicked.connect(self._on_browse_mask_dir)
        row_mask_dir.addWidget(self.txt_mask_dir_step3)
        row_mask_dir.addWidget(btn_browse_mask_dir)
        f_paths.addRow("Masks Directory:", row_mask_dir)

        # Mask Extension
        self.txt_mask_ext = QLineEdit(self.starlight_config.mask_ext)
        self.txt_mask_ext.setPlaceholderText(".mask")
        f_paths.addRow("Mask Extension:", self.txt_mask_ext)"""

gcontent = gcontent.replace(old_mask, new_mask)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

