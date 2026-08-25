import re

gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

old_logic = """            # Automatically persist mask
            if spec_path and len(self.spectral_mask.intervals) > 0:
                mask_ext = self.starlight_config.mask_ext or ".mask"
                if not mask_ext.startswith('.'): mask_ext = "." + mask_ext
                spec_base = os.path.splitext(os.path.basename(spec_path))[0]
                
                if mask_dir:
                    import os
                    os.makedirs(mask_dir, exist_ok=True)
                    auto_mask = os.path.join(mask_dir, f"{spec_base}{mask_ext}")"""

new_logic = """            # Automatically persist mask
            if spec_path and len(self.spectral_mask.intervals) > 0:
                mask_ext = self.starlight_config.mask_ext or ".mask"
                if not mask_ext.startswith('.'): mask_ext = "." + mask_ext
                spec_base = os.path.splitext(os.path.basename(spec_path))[0]
                
                # Fetch mask_dir from the dialog just in case the user edited it
                final_mask_dir = dlg.txt_dlg_mask_dir.text().strip() if hasattr(dlg, 'txt_dlg_mask_dir') else mask_dir
                
                if final_mask_dir:
                    import os
                    os.makedirs(final_mask_dir, exist_ok=True)
                    auto_mask = os.path.join(final_mask_dir, f"{spec_base}{mask_ext}")
                    # Update main window field
                    if hasattr(self, 'txt_mask_dir_step2'):
                        self.txt_mask_dir_step2.setText(final_mask_dir)"""

gcontent = gcontent.replace(old_logic, new_logic)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

