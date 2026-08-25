"""
Starlight Runner — A modern workflow & GUI suite for STARLIGHT stellar population synthesis.
Includes data preprocessing, spectral masking, grid runner, and output analysis (PyLight).
"""

__version__ = "1.0.0"
__author__ = "Rogério Riffel"

import os as _os

PACKAGE_DIR = _os.path.dirname(_os.path.abspath(__file__))
PROJECT_DIR = _os.path.dirname(PACKAGE_DIR)
TEMPLATES_DIR = _os.path.join(PACKAGE_DIR, "templates")
ASSETS_DIR = _os.path.join(PACKAGE_DIR, "assets")
