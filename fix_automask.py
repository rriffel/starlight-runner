import re

gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

old_logic = """            # Automatically persist mask with spectrum name (<spec_base>.sm)
            if spec_path and len(self.spectral_mask.intervals) > 0:
                spec_dir = os.path.dirname(spec_path)
                spec_base = os.path.splitext(os.path.basename(spec_path))[0]
                auto_mask = os.path.join(spec_dir, f"{spec_base}.sm") if spec_dir else f"{spec_base}.sm"
                try:
                    self.spectral_mask.save_to_file(auto_mask)
                    rel_mask = os.path.basename(auto_mask)
                    self.starlight_config.mask_file = rel_mask
                    if hasattr(self, 'txt_mask_file'):
                        self.txt_mask_file.setText(rel_mask)
                    self.statusBar().showMessage(f"✅ Máscara salva automaticamente: {auto_mask} ({len(self.spectral_mask.intervals)} intervalos)")
                except Exception as e:
                    self.statusBar().showMessage(f"Edição de máscaras concluída ({len(self.spectral_mask.intervals)} intervalos).")"""

new_logic = """            # Automatically persist mask
            if spec_path and len(self.spectral_mask.intervals) > 0:
                mask_ext = self.starlight_config.mask_ext
                if not mask_ext.startswith('.'): mask_ext = "." + mask_ext
                spec_base = os.path.splitext(os.path.basename(spec_path))[0]
                
                if mask_dir:
                    import os
                    os.makedirs(mask_dir, exist_ok=True)
                    auto_mask = os.path.join(mask_dir, f"{spec_base}{mask_ext}")
                else:
                    spec_dir = os.path.dirname(spec_path)
                    auto_mask = os.path.join(spec_dir, f"{spec_base}{mask_ext}") if spec_dir else f"{spec_base}{mask_ext}"

                try:
                    self.spectral_mask.save_to_file(auto_mask)
                    self.statusBar().showMessage(f"✅ Auto-saved mask: {auto_mask} ({len(self.spectral_mask.intervals)} intervals)")
                except Exception as e:
                    self.statusBar().showMessage(f"Masking done ({len(self.spectral_mask.intervals)} intervals).")"""

gcontent = gcontent.replace(old_logic, new_logic)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

