import re

gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

# 1. Fix Sidebar Layout
old_sidebar = """        for text, idx in steps:
            btn = QPushButton(text)
            btn.setObjectName("navBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx: self.set_active_page(i))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)


        layout.addStretch()
        
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

new_sidebar = """        for text, idx in steps:
            btn = QPushButton(text)
            btn.setObjectName("navBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx: self.set_active_page(i))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addSpacing(20)

        # Global Config Buttons (Moved up so they don't get clipped on small screens)
        lbl_cfg = QLabel("Global Configuration")
        lbl_cfg.setStyleSheet(f"color: {ACCENT}; font-size: 11px; font-weight: bold; margin-bottom: 2px;")
        layout.addWidget(lbl_cfg)
        
        btn_load_cfg = QPushButton("Load Config State")
        btn_load_cfg.clicked.connect(self._on_load_config_state)
        layout.addWidget(btn_load_cfg)
        
        btn_save_cfg = QPushButton("Save Config State")
        btn_save_cfg.clicked.connect(self._on_save_config_state)
        layout.addWidget(btn_save_cfg)

        layout.addStretch()

        # Footer info"""
gcontent = gcontent.replace(old_sidebar, new_sidebar)

# 2. Fix Worker Thread
old_worker = """    def run(self):
        total = len(self.grid_files)
        self.log_message.emit(f"🚀 Starting STARLIGHT execution on {total} grid file(s)...")

        for idx, g in enumerate(self.grid_files, 1):
            if self._is_cancelled:
                self.log_message.emit("⚠️ Batch execution cancelled by user.")
                break

            self.log_message.emit(f"[{idx}/{total}] Running grid: {os.path.basename(g)}...")
            res = run_single_grid(g, self.starlight_exe, self.cwd)
            self.grid_finished.emit(res)
            
            if res["returncode"] == 0:
                self.log_message.emit(f"✅ Finished: {os.path.basename(g)}")
            else:
                self.log_message.emit(f"❌ Error in {os.path.basename(g)} (code {res['returncode']}): {res['stderr']}")

        self.all_finished.emit()"""

new_worker = """    def run(self):
        import subprocess
        total = len(self.grid_files)
        self.log_message.emit(f"🚀 Starting STARLIGHT execution on {total} grid file(s)...")

        for idx, g in enumerate(self.grid_files, 1):
            if self._is_cancelled:
                self.log_message.emit("⚠️ Batch execution cancelled by user.")
                break

            self.log_message.emit(f"[{idx}/{total}] Running grid: {os.path.basename(g)}...")
            
            exe_path = os.path.abspath(os.path.join(self.cwd, self.starlight_exe)) if not os.path.isabs(self.starlight_exe) else self.starlight_exe
            if not os.path.exists(exe_path):
                exe_path = self.starlight_exe

            with open(g, 'r') as grid_in:
                process = subprocess.Popen(
                    [exe_path],
                    stdin=grid_in,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=self.cwd,
                    text=True,
                    bufsize=1
                )
                
                # Stream output line by line
                for line in process.stdout:
                    if self._is_cancelled:
                        process.terminate()
                        break
                    # Emit line without trailing newline since append() adds one
                    self.log_message.emit(line.rstrip('\\n'))
                
                process.wait()
                
            res = {"grid": g, "returncode": process.returncode}
            self.grid_finished.emit(res)
            
            if process.returncode == 0:
                self.log_message.emit(f"✅ Finished: {os.path.basename(g)}\\n")
            else:
                self.log_message.emit(f"❌ Error in {os.path.basename(g)} (code {process.returncode})\\n")

        self.all_finished.emit()"""
gcontent = gcontent.replace(old_worker, new_worker)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

