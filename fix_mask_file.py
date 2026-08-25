runner_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/runner.py"
with open(runner_path, "r", encoding="utf-8") as f:
    rcontent = f.read()
    
rcontent = rcontent.replace('self.mask_file = kwargs.get("mask_file", "mask.sm")', 'self.mask_ext = kwargs.get("mask_ext", ".sm")')

with open(runner_path, "w", encoding="utf-8") as f:
    f.write(rcontent)
