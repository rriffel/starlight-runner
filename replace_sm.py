import os
import glob

files = glob.glob("/home/riffel/Dropbox/programas/Develp/starlight-runner/**/*.py", recursive=True)

for file_path in files:
    # Skip patch files
    if os.path.basename(file_path).startswith("patch_") or os.path.basename(file_path).startswith("fix_") or os.path.basename(file_path).startswith("test_"):
        continue

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content.replace("'.mask'", "'.mask'")
    new_content = new_content.replace('".mask"', '".mask"')
    new_content = new_content.replace("*.mask", "*.mask")
    new_content = new_content.replace("mask.mask", "mask.mask")
    new_content = new_content.replace("(.mask)", "(.mask)")

    # specific replacements
    new_content = new_content.replace("Starlight .mask", "Starlight .mask")
    new_content = new_content.replace("Load .mask", "Load .mask")
    new_content = new_content.replace("Save .mask", "Save .mask")
    new_content = new_content.replace("Salvar .mask", "Salvar .mask")
    new_content = new_content.replace("Carregar .mask", "Carregar .mask")
    new_content = new_content.replace("starlightMask(filename,maskname='mask.mask'", "starlightMask(filename,maskname='mask.mask'") # redundant but fine

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file_path}")

print("Done.")
