"""
main_gui.py — Main Graphical User Interface for STARLIGHT Spectral Fitting & Workflow.
Features a 4-step scientific workflow:
  Step 1: Data Preprocessing (Galactic dereddening, restframe shift, rebinning, telluric cut)
  Step 2: Masking & Spectral Regions (Interactive & presets for emission lines/tellurics)
  Step 3: STARLIGHT Grid Setup & Multithread Execution (Config generator, parallel runner)
  Step 4: Output Analysis & Stellar Populations (Synthetic spectrum, residuals, population vectors)
"""

import sys
import os

if __package__ is None or __package__ == "":
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    __package__ = "starlight_runner"

import glob
import traceback
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPixmap

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from .masking import SpectralMask
from .pylight_reader import default_pylight_config
from .runner import StarlightConfig

# Shared styling constants & light/dark theming
from .gui import constants

# Mixin classes (each implements one tab/step)
from .gui.preprocessing_mixin import PreprocessingMixin
from .gui.masking_mixin import MaskingMixin
from .gui.grid_mixin import GridMixin
from .gui.results_mixin import ResultsMixin
from .gui.config_mixin import ConfigMixin


def get_logo_path():
    """Locate the logo image file from package assets or project directories."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "assets", "logo.png"),
        os.path.join(os.path.dirname(__file__), "assets", "logo.jpeg"),
        os.path.join(os.path.dirname(__file__), "assets", "logo.jpg"),
        os.path.join(os.path.dirname(__file__), "..", "logo.png"),
        os.path.join(os.path.dirname(__file__), "..", "logo.jpeg"),
        os.path.join(os.path.dirname(__file__), "..", "logo.jpg"),
        os.path.join(os.getcwd(), "logo.png"),
        os.path.join(os.getcwd(), "logo.jpeg"),
        os.path.join(os.getcwd(), "logo.jpg"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return None


class MainWindow(QMainWindow, PreprocessingMixin, MaskingMixin, GridMixin, ResultsMixin, ConfigMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STARLIGHT Stellar Population Runner & Analyser")
        logo_path = get_logo_path()
        if logo_path:
            self.setWindowIcon(QIcon(logo_path))

        # Pylight Configuration (from ConfigPylight); same defaults as the scripting API
        self.pylight_config = default_pylight_config()


        self.resize(1350, 900)
        constants.apply_theme(QApplication.instance())

        # State variables
        self.current_spectrum_path = None
        self.raw_wl = None
        self.raw_flux = None
        self.raw_eflux = None

        self.proc_wl = None
        self.proc_flux = None
        self.proc_eflux = None

        # Interactive telluric cuts & boundary trimming
        self.telluric_cuts = []  # list of {"low": float, "upp": float, "name": str}
        self.preproc_click_pt = None
        self.ax_preproc = None

        # Interactive masking
        self.mask_click_pt = None
        self.ax_mask = None


        self.spectral_mask = SpectralMask()
        self.starlight_config = StarlightConfig()
        self.parsed_output = None
        self.batch_outputs = pd.DataFrame()

        self.worker_thread = None

        # Build UI
        self._init_ui()


    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar navigation
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # Stacked Pages
        self.pages = QStackedWidget(self)
        self.page_preprocess = self._create_step1_preprocess()
        self.page_masking = self._create_step2_masking()
        self.page_runner = self._create_step3_runner()
        self.page_results = self._create_step4_results()
        self._sync_pylight_zs()  # PyLight metallicities = unique Z of the Step 3 Base File

        self.pages.addWidget(self.page_preprocess)
        self.pages.addWidget(self.page_masking)
        self.pages.addWidget(self.page_runner)
        self.pages.addWidget(self.page_results)

        main_layout.addWidget(self.pages, 1)

        # Status Bar
        self.statusBar().showMessage("Ready — Select or load a spectrum to begin.")
        self.set_active_page(0)

    def _create_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setAttribute(Qt.WA_StyledBackground, True)
        sidebar.setProperty("role", "sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(8)

        # App Title
        title_label = QLabel("STARLIGHT")
        title_label.setProperty("role", "accentLabel")
        title_label.setStyleSheet("font-size: 18px; font-weight: 800; margin-bottom: 2px;")
        sub_label = QLabel("Runner & Analyser v1.0")
        sub_label.setProperty("role", "mutedLabel")
        sub_label.setStyleSheet("font-size: 11px; margin-bottom: 8px;")
        layout.addWidget(title_label)
        layout.addWidget(sub_label)

        # Inset Logo before Step 1
        logo_path = get_logo_path()
        if logo_path:
            logo_pix = QPixmap(logo_path)
            if not logo_pix.isNull():
                lbl_logo = QLabel()
                scaled_pix = logo_pix.scaledToWidth(190, Qt.SmoothTransformation)
                lbl_logo.setPixmap(scaled_pix)
                lbl_logo.setAlignment(Qt.AlignCenter)
                lbl_logo.setStyleSheet("background: transparent; border: none; margin-bottom: 12px;")
                layout.addWidget(lbl_logo)

        # Step Navigation Buttons
        self.nav_buttons = []
        steps = [
            ("1. Data Preprocessing", 0),
            ("2. Spectral Masking", 1),
            ("3. STARLIGHT Grid", 2),
            ("4. Results & Analysis", 3)
        ]

        for text, idx in steps:
            btn = QPushButton(text)
            btn.setObjectName("navBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx: self.set_active_page(i))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addSpacing(20)

        # Global Config Buttons (Moved up so they don't get clipped on small screens)
        lbl_cfg = QLabel("Global Configuration")
        lbl_cfg.setProperty("role", "accentLabel")
        lbl_cfg.setStyleSheet("font-size: 11px; font-weight: bold; margin-bottom: 2px;")
        layout.addWidget(lbl_cfg)
        
        btn_load_cfg = QPushButton("Load Config State")
        btn_load_cfg.setProperty("role", "secondaryBtn")
        btn_load_cfg.setCursor(Qt.PointingHandCursor)
        btn_load_cfg.clicked.connect(self._on_load_config_state)
        layout.addWidget(btn_load_cfg)
        
        btn_save_cfg = QPushButton("Save Config State")
        btn_save_cfg.setProperty("role", "secondaryBtn")
        btn_save_cfg.setCursor(Qt.PointingHandCursor)
        btn_save_cfg.clicked.connect(self._on_save_config_state)
        layout.addWidget(btn_save_cfg)

        # Run scripts (.py): standalone, GUI-free; can be loaded back (as in urutau)
        btn_export_script = QPushButton("Export Script (.py)")
        btn_export_script.setProperty("role", "secondaryBtn")
        btn_export_script.setCursor(Qt.PointingHandCursor)
        btn_export_script.setToolTip("Write the Step 3 / PyLight configuration as a Python script that runs\n"
                                     "STARLIGHT without the GUI (python run_starlight.py)")
        btn_export_script.clicked.connect(self._on_export_script)
        layout.addWidget(btn_export_script)

        btn_load_script = QPushButton("Load Script (.py)")
        btn_load_script.setProperty("role", "secondaryBtn")
        btn_load_script.setCursor(Qt.PointingHandCursor)
        btn_load_script.setToolTip("Fill the GUI from a run script (runs the script's code; STARLIGHT is not run)")
        btn_load_script.clicked.connect(self._on_load_script)
        layout.addWidget(btn_load_script)

        layout.addSpacing(12)

        # Appearance
        lbl_appearance = QLabel("Appearance")
        lbl_appearance.setProperty("role", "accentLabel")
        lbl_appearance.setStyleSheet("font-size: 11px; font-weight: bold; margin-bottom: 2px;")
        layout.addWidget(lbl_appearance)

        self.chk_dark_mode = QCheckBox("  Dark Mode")
        self.chk_dark_mode.setChecked(constants.is_dark())
        self.chk_dark_mode.toggled.connect(self._on_toggle_theme)
        layout.addWidget(self.chk_dark_mode)

        layout.addStretch()

        # Footer info
        footer = QLabel("Rogério Riffel\nUFRGS / Depto Astronomia")
        footer.setProperty("role", "mutedLabel")
        footer.setStyleSheet("font-size: 11px; line-height: 1.4;")
        layout.addWidget(footer)

        return sidebar

    def _on_toggle_theme(self, checked):
        """Switch between light and dark mode."""
        constants.apply_theme(QApplication.instance(), dark=checked)

    def set_active_page(self, index):
        prev_index = self.pages.currentIndex()

        # Prompt to save mask when leaving Step 2 (Masking) towards Step 3 (Grid)
        if prev_index == 1 and index == 2 and self.spectral_mask.intervals:
            reply = QMessageBox.question(
                self,
                "Save Spectral Mask",
                "Do you want to save the spectral mask (.mask) before\n"
                "proceeding to the STARLIGHT Grid step?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._on_save_sm_dialog()
            elif reply == QMessageBox.Cancel:
                return  # abort navigation

        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if index == 1:
            # Sync Step 2 (Masking)
            if hasattr(self, 'lbl_mask_loaded_file'):
                if self.current_spectrum_path:
                    self.lbl_mask_loaded_file.setText(os.path.basename(self.current_spectrum_path))
                elif self.proc_wl is not None or self.raw_wl is not None:
                    self.lbl_mask_loaded_file.setText("Active spectrum in memory")
            self._plot_masking()
        elif index == 2:
            # Sync Step 3 (Runner) observation directory if available
            if hasattr(self, 'txt_obs_dir') and self.current_spectrum_path:
                obs_d = os.path.dirname(os.path.abspath(self.current_spectrum_path))
                if obs_d and os.path.exists(obs_d):
                    self.txt_obs_dir.setText(obs_d)
                    self.starlight_config.obs_dir = obs_d
            if hasattr(self, '_update_mc_availability'):
                self._update_mc_availability()
        elif index == 3:
            # Sync Step 4 (Results)
            if hasattr(self, '_plot_results') and self.parsed_output is not None:
                self._plot_results()


    # -------------------------------------------------------------
    # STEP 1: PREPROCESSING PAGE
    # -------------------------------------------------------------

def main():
    if "--test" in sys.argv or "-t" in sys.argv:
        from .tests import run_tests
        success = run_tests()
        sys.exit(0 if success else 1)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("STARLIGHT Runner & Analyser")
    
    # Configure global font
    font = QFont("Inter", 10)
    app.setFont(font)

    # Set Window / App Icon
    logo_path = get_logo_path()
    if logo_path:
        app.setWindowIcon(QIcon(logo_path))

    # Startup Splash Screen
    splash = None
    if logo_path:
        logo_pix = QPixmap(logo_path)
        if not logo_pix.isNull():
            splash_pix = logo_pix.scaledToWidth(480, Qt.SmoothTransformation)
            splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
            splash.showMessage(
                "  STARLIGHT Runner & Analyser — Initializing...",
                Qt.AlignBottom | Qt.AlignLeft,
                QColor("#FFFFFF")
            )
            splash.show()
            app.processEvents()
    
    window = MainWindow()
    if splash:
        splash.finish(window)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
