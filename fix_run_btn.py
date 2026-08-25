import re

gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

old_run = """    def _on_run_starlight_clicked(self):
        grid_files = sorted(glob.glob("grid_*.inp"))
        if not grid_files:
            QMessageBox.warning(self, "No Grid Files", "Please generate or create grid_*.inp files first.")
            return

        self._sync_config_from_ui()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(grid_files))

        self.worker_thread = StarlightWorkerThread("""

new_run = """    def _on_run_starlight_clicked(self):
        reply = QMessageBox.question(
            self,
            "Gerar Grids e Salvar?",
            "Deseja gerar novos arquivos de Grid e salvar a configuração Global antes de rodar o STARLIGHT?\\n(Isso previne que você rode o modelo com configurações velhas).",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Cancel:
            return
        elif reply == QMessageBox.Yes:
            self._on_generate_grids()
            self._on_save_config_state()

        grid_files = sorted(glob.glob("grid_*.inp"))
        if not grid_files:
            QMessageBox.warning(self, "No Grid Files", "Please generate or create grid_*.inp files first.")
            return

        self._sync_config_from_ui()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(grid_files))

        self.worker_thread = StarlightWorkerThread("""

gcontent = gcontent.replace(old_run, new_run)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

