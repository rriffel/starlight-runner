import re

file_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

validation_code = """
    def _validate_bases(self):
        base_file = self.txt_base_file.text().strip()
        base_dir = self.txt_base_dir.text().strip()
        
        if not base_file or not os.path.exists(base_file):
            return False, f"Base Manifest File not found: {base_file}"
            
        if not base_dir or not os.path.exists(base_dir):
            return False, f"Bases Directory not found: {base_dir}"
            
        missing_files = []
        try:
            with open(base_file, 'r') as f:
                lines = f.readlines()
                
            is_first_line = True
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                tokens = line.split()
                if is_first_line:
                    if len(tokens) <= 2 and tokens[0].isdigit():
                        is_first_line = False
                        continue
                    is_first_line = False
                
                base_filename = tokens[0]
                if not os.path.exists(os.path.join(base_dir, base_filename)):
                    missing_files.append(base_filename)
                    
            if missing_files:
                err_msg = f"Found {len(missing_files)} missing base files in '{base_dir}'.\\n\\nFirst few missing:\\n"
                for m in missing_files[:5]:
                    err_msg += f"- {m}\\n"
                if len(missing_files) > 5:
                    err_msg += "..."
                return False, err_msg
                
            return True, "All base files present."
        except Exception as e:
            return False, f"Error validating bases: {str(e)}"

    def _on_generate_grids(self):"""

content = content.replace("    def _on_generate_grids(self):", validation_code)

validation_check = """        self.starlight_config.obs_dir = obs_dir

        is_valid, msg = self._validate_bases()
        if not is_valid:
            QMessageBox.critical(self, "Bases Validation Failed", msg)
            return

        try:
            grids = generate_grid_files(spec_files, self.starlight_config)"""

old_grid_gen = """        self.starlight_config.obs_dir = obs_dir

        try:
            grids = generate_grid_files(spec_files, self.starlight_config)"""

content = content.replace(old_grid_gen, validation_check)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Validation patch applied!")
