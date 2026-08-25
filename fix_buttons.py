import re

gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

old_btns = """        btn_load_cfg = QPushButton("Load Config State")
        btn_load_cfg.clicked.connect(self._on_load_config_state)
        layout.addWidget(btn_load_cfg)
        
        btn_save_cfg = QPushButton("Save Config State")
        btn_save_cfg.clicked.connect(self._on_save_config_state)
        layout.addWidget(btn_save_cfg)"""

new_btns = """        btn_load_cfg = QPushButton("Load Config State")
        btn_load_cfg.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px; color: #334155;")
        btn_load_cfg.setCursor(Qt.PointingHandCursor)
        btn_load_cfg.clicked.connect(self._on_load_config_state)
        layout.addWidget(btn_load_cfg)
        
        btn_save_cfg = QPushButton("Save Config State")
        btn_save_cfg.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px; color: #334155;")
        btn_save_cfg.setCursor(Qt.PointingHandCursor)
        btn_save_cfg.clicked.connect(self._on_save_config_state)
        layout.addWidget(btn_save_cfg)"""

gcontent = gcontent.replace(old_btns, new_btns)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

