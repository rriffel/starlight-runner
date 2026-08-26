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
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from .masking import SpectralMask
from .runner import StarlightConfig

# Shared styling constants
from .gui.constants import (
    ACCENT, ACCENT_HOVER, DARK_BG, CARD_BG, TEXT_COLOR,
    MUTED, BORDER_COLOR, SUCCESS_COLOR, DANGER_COLOR, STYLESHEET
)

# Mixin classes (each implements one tab/step)
from .gui.preprocessing_mixin import PreprocessingMixin
from .gui.masking_mixin import MaskingMixin
from .gui.grid_mixin import GridMixin
from .gui.results_mixin import ResultsMixin
from .gui.config_mixin import ConfigMixin





class MainWindow(QMainWindow, PreprocessingMixin, MaskingMixin, GridMixin, ResultsMixin, ConfigMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Starlight stellar population runner & analyser")

        # Pylight Configuration (from ConfigPylight)
        self.pylight_config = {
            'Zs': [0.00382, 0.00959, 0.0152, 0.02409],
            'IsAGNComp': True,
            'OnlyFC': False,
            'pltmask': False,
            'NormFac': 1,
            'SaveDist': True,
            'zsun': 0.0152,
            'BinPopVecLab': ['xy', 'xiy', 'xio', 'xo'],
            'BinPopVecMassLab': ['my', 'miy', 'mio', 'mo'],
            'BinPopVec': {'xy': [1E3, 100e6], 'xiy': [101e6, 700e6], 'xio': [750E6, 2E9], 'xo': [2.10e9, 15e9]},
            'BinSFRLabs': ['SFR_1E6', 'SFR_5E6', 'SFR_10E6', 'SFR_14E6', 'SFR_20E6', 'SFR_30E6', 'SFR_56E6', 'SFR_100E6', 'SFR_200E6'],
            'BinSFR': {"SFR_1E6": [10,1.001E6], "SFR_5E6": [10,5.621E6], "SFR_10E6": [10,10.001E6],"SFR_14E6":[10,14.1001E6],"SFR_20E6": [10,20.001E6],"SFR_30E6": [10,31.6001E6],"SFR_56E6": [10,56.201E6],"SFR_100E6":[10,100.001E6],"SFR_200E6": [10,200.001E6]},
            'BinHDVecLab': ['BB_c', 'BB_h', 'HDTot'],
            'BinHDVec': {'BB_c': [0, 1000], 'BB_h': [1000, 1500], 'HDTot': [0, 1500]},
            'BinFCVecLab': ['FC1.25', 'FC1.50', 'FC1.75', 'FCTot'],
            'BinFCVec': {'FC1.25': [0, 1.25], 'FC1.50': [1.26, 1.50], 'FC1.75': [1.51, 1.75], 'FCTot': [0, 1.76]}
        }


        self.resize(1350, 900)
        self.setStyleSheet(STYLESHEET)

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
        sidebar.setStyleSheet(f"background-color: {CARD_BG}; border-right: 1px solid {BORDER_COLOR};")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(8)

        # App Title
        title_label = QLabel("STARLIGHT")
        title_label.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {ACCENT}; margin-bottom: 2px;")
        sub_label = QLabel("Runner & Analyser v1.0")
        sub_label.setStyleSheet(f"font-size: 11px; color: {MUTED}; margin-bottom: 16px;")
        layout.addWidget(title_label)
        layout.addWidget(sub_label)

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
        lbl_cfg.setStyleSheet(f"color: {ACCENT}; font-size: 11px; font-weight: bold; margin-bottom: 2px;")
        layout.addWidget(lbl_cfg)
        
        btn_load_cfg = QPushButton("Load Config State")
        btn_load_cfg.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px; color: #334155;")
        btn_load_cfg.setCursor(Qt.PointingHandCursor)
        btn_load_cfg.clicked.connect(self._on_load_config_state)
        layout.addWidget(btn_load_cfg)
        
        btn_save_cfg = QPushButton("Save Config State")
        btn_save_cfg.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px; color: #334155;")
        btn_save_cfg.setCursor(Qt.PointingHandCursor)
        btn_save_cfg.clicked.connect(self._on_save_config_state)
        layout.addWidget(btn_save_cfg)

        layout.addStretch()

        # Footer info
        footer = QLabel("Rogério Riffel\nUFRGS / Depto Astronomia")
        footer.setStyleSheet(f"color: {MUTED}; font-size: 11px; line-height: 1.4;")
        layout.addWidget(footer)

        return sidebar

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
        elif index == 3:
            # Sync Step 4 (Results)
            if hasattr(self, '_plot_results') and self.parsed_output is not None:
                self._plot_results()


    # -------------------------------------------------------------
    # STEP 1: PREPROCESSING PAGE
    # -------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Configure global font
    font = QFont("Inter", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
