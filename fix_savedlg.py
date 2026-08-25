import re

gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

old_logic = """        if spec_path:
            spec_base = os.path.splitext(os.path.basename(spec_path))[0]
            if mask_dir:
                default_name = os.path.join(mask_dir, f"{spec_base}{mask_ext}")
            else:
                spec_dir = os.path.dirname(spec_path)
                default_name = os.path.join(spec_dir, f"{spec_base}{mask_ext}") if spec_dir else f"{spec_base}{mask_ext}\""""

new_logic = """        if spec_path:
            spec_base = os.path.splitext(os.path.basename(spec_path))[0]
            if mask_dir:
                import os
                os.makedirs(mask_dir, exist_ok=True)
                default_name = os.path.join(mask_dir, f"{spec_base}{mask_ext}")
            else:
                spec_dir = os.path.dirname(spec_path)
                default_name = os.path.join(spec_dir, f"{spec_base}{mask_ext}") if spec_dir else f"{spec_base}{mask_ext}\""""

gcontent = gcontent.replace(old_logic, new_logic)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

