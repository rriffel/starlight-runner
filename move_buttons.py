import re

gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

# 1. Remove from Step 3
old_step3_btns = """        # Action Buttons
        row_cfg_btns = QHBoxLayout()
        btn_load_cfg = QPushButton("Load Config State")
        btn_load_cfg.clicked.connect(self._on_load_config_state)
        btn_save_cfg = QPushButton("Save Config State")
        btn_save_cfg.clicked.connect(self._on_save_config_state)
        row_cfg_btns.addWidget(btn_load_cfg)
        row_cfg_btns.addWidget(btn_save_cfg)
        left_layout.addLayout(row_cfg_btns)"""

gcontent = gcontent.replace(old_step3_btns, "")

# 2. Add to Sidebar
old_sidebar_stretch = """        layout.addStretch()

        # Footer info"""

new_sidebar_stretch = """        layout.addStretch()
        
        # Global Config Buttons
        lbl_cfg = QLabel("Global Configuration")
        lbl_cfg.setStyleSheet(f"color: {ACCENT}; font-size: 11px; font-weight: bold; margin-bottom: 2px;")
        layout.addWidget(lbl_cfg)
        
        btn_load_cfg = QPushButton("Load Config State")
        btn_load_cfg.clicked.connect(self._on_load_config_state)
        layout.addWidget(btn_load_cfg)
        
        btn_save_cfg = QPushButton("Save Config State")
        btn_save_cfg.clicked.connect(self._on_save_config_state)
        layout.addWidget(btn_save_cfg)
        
        layout.addSpacing(10)

        # Footer info"""

gcontent = gcontent.replace(old_sidebar_stretch, new_sidebar_stretch)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

