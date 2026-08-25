import re

gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

old_toolbar = """        # Top Toolbar (Weight radio buttons, Presets, Save, Close)
        toolbar = QHBoxLayout()
        
        lbl_mode = QLabel("<b>Left Click:</b>")
        self.radio_0 = QRadioButton("Weight 0.0 (Red - Exclude)")"""

new_toolbar = """        # Top Toolbar (Weight radio buttons, Presets, Save, Close)
        toolbar = QHBoxLayout()
        
        lbl_mdir = QLabel("Mask Dir:")
        self.txt_dlg_mask_dir = QLineEdit(mask_dir or "")
        self.txt_dlg_mask_dir.setPlaceholderText("Directory to save masks...")
        self.txt_dlg_mask_dir.setFixedWidth(150)
        toolbar.addWidget(lbl_mdir)
        toolbar.addWidget(self.txt_dlg_mask_dir)
        toolbar.addSpacing(10)

        lbl_mode = QLabel("<b>Left Click:</b>")
        self.radio_0 = QRadioButton("Weight 0.0 (Red - Exclude)")"""

gcontent = gcontent.replace(old_toolbar, new_toolbar)

old_save_action = """        if self.spectrum_path:
            self.spectral_mask.save_to_file(self.default_mask_path)
            QMessageBox.information(self, "Saved", f"Mask saved automatically to:\\n{self.default_mask_path}")"""

new_save_action = """        if self.spectrum_path:
            mask_ext = getattr(self.parent(), 'starlight_config', None)
            mask_ext = mask_ext.mask_ext if mask_ext else ".mask"
            if not mask_ext.startswith('.'): mask_ext = "." + mask_ext
            
            spec_base = os.path.splitext(os.path.basename(self.spectrum_path))[0]
            new_mask_dir = self.txt_dlg_mask_dir.text().strip()
            if new_mask_dir:
                import os
                os.makedirs(new_mask_dir, exist_ok=True)
                save_path = os.path.join(new_mask_dir, f"{spec_base}{mask_ext}")
                
                # Sync back to main window if parent has it
                if hasattr(self.parent(), 'txt_mask_dir_step2'):
                    self.parent().txt_mask_dir_step2.setText(new_mask_dir)
            else:
                spec_dir = os.path.dirname(self.spectrum_path)
                save_path = os.path.join(spec_dir, f"{spec_base}{mask_ext}") if spec_dir else f"{spec_base}{mask_ext}"

            self.spectral_mask.save_to_file(save_path)
            QMessageBox.information(self, "Saved", f"Mask saved automatically to:\\n{save_path}")"""
gcontent = gcontent.replace(old_save_action, new_save_action)

# Update _on_save_sm logic to read the dialog's txt_dlg_mask_dir as well if they use the "Save .sm" button.
# "Save .sm" button is in InteractiveMaskDialog and calls `_on_save_sm`

old_on_save = """    def _on_save_sm(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save STARLIGHT Mask", self.default_mask_path, "Starlight Mask (*.sm);;All Files (*)"
        )
        if filepath:
            self.spectral_mask.save_to_file(filepath)
            self.default_mask_path = filepath
            QMessageBox.information(self, "Saved", f"Mask saved to:\\n{filepath}")"""

new_on_save = """    def _on_save_sm(self):
        mask_ext = getattr(self.parent(), 'starlight_config', None)
        mask_ext = mask_ext.mask_ext if mask_ext else ".mask"
        if not mask_ext.startswith('.'): mask_ext = "." + mask_ext
        
        current_mdir = self.txt_dlg_mask_dir.text().strip()
        default_save = self.default_mask_path
        if self.spectrum_path and current_mdir:
            spec_base = os.path.splitext(os.path.basename(self.spectrum_path))[0]
            import os
            os.makedirs(current_mdir, exist_ok=True)
            default_save = os.path.join(current_mdir, f"{spec_base}{mask_ext}")
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save STARLIGHT Mask", default_save, f"Starlight Mask (*{mask_ext});;All Files (*)"
        )
        if filepath:
            self.spectral_mask.save_to_file(filepath)
            self.default_mask_path = filepath
            QMessageBox.information(self, "Saved", f"Mask saved to:\\n{filepath}")
            
            # Sync back to main window if parent has it
            if current_mdir and hasattr(self.parent(), 'txt_mask_dir_step2'):
                self.parent().txt_mask_dir_step2.setText(current_mdir)"""
gcontent = gcontent.replace(old_on_save, new_on_save)


with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

print("Dialog patched.")
