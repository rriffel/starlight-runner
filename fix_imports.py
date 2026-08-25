gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

bad_import = """if __package__ is None or __package__ == "":
    import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ReadStarlightParameters import starlightPars, popVectors, StSyntesis
    from pathlib import Path"""

good_import = """import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ReadStarlightParameters import starlightPars, popVectors, StSyntesis

if __package__ is None or __package__ == "":
    from pathlib import Path"""

gcontent = gcontent.replace(bad_import, good_import)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)
