import os
import re

base_file = "/home/riffel/Dropbox/programas/Develp/starlight-runner/BasesXSLKrupaPCRR"
base_dir = "/home/riffel/Dropbox/programas/Develp/starlight-runner/BasesDir"

missing = []
with open(base_file, 'r') as f:
    lines = f.readlines()

is_first_line = True
for line in lines:
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    tokens = line.split()
    if is_first_line:
        # Check if first line is N_base
        if len(tokens) <= 2 and tokens[0].isdigit():
            is_first_line = False
            continue
        is_first_line = False
    
    base_filename = tokens[0]
    # Check if base_filename exists in base_dir
    if not os.path.exists(os.path.join(base_dir, base_filename)):
        missing.append(base_filename)

print(f"Missing {len(missing)} files. First few: {missing[:5]}")
