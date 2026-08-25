# Starlight Runner

A modern workflow and graphical interface suite for **STARLIGHT** stellar population synthesis models.
Provides end-to-end data preparation, extinction correction, interactive spectral masking, automated multi-core grid execution, and comprehensive population synthesis diagnostics (PyLight).

---

## 🚀 Key Features

* **Complete 4-Step Scientific Pipeline:** Smooth workflow from raw spectrum ingestion to publication-ready population synthesis figures and tables.
* **Interstellar Extinction Laws:** Built-in Cardelli et al. (1989), Calzetti et al. (2000), Fitzpatrick (1999), Seaton (1979), and Gordon et al. (2024 SMC).
* **Rest-Frame & Rebinning:** Fast redshift shifting ($\lambda_{\text{rest}} = \lambda / (1+z)$) and linear/spline flux & error interpolation with customizable $\Delta\lambda$.
* **Spectral Masking Studio:** Standard presets for Optical and NIR emission lines / telluric gaps, plus interactive table and graphical interval editor with weight control (0 = exclude, 2 = key line).
* **Automated Grid Generation & Parallel Execution:** Auto-partitions spectrum lists across CPU cores and manages STARLIGHT Fortran binary execution in the background with a live diagnostics console.
* **Results & Stellar Population Explorer:** Reads Starlight `.out` files (V4 & V5), plots observed vs. synthetic spectrum, residual spectrum ($O - S$), and decomposes light ($x_j$) and mass ($m_j$) fractions by age and metallicity bins.

---

## 📦 Installation

Install directly in development (editable) mode:

```bash
git clone https://github.com/rriffel/starlight-runner.git
cd starlight-runner
pip install -e .
```

Or install dependencies with `pip`:
```bash
pip install -r requirements.txt
```

---

## 🖥️ Running the Application

### 1. Graphical User Interface (GUI)
Launch the studio directly from your terminal:
```bash
starlight-runner
```
or
```bash
python -m starlight_runner
```

### 2. Python API
All components are modular and can be used directly in Python scripts or Jupyter Notebooks:

```python
from starlight_runner.preprocessing import preprocess_pipeline
from starlight_runner.masking import SpectralMask
from starlight_runner.runner import StarlightConfig, generate_grid_files
from starlight_runner.parser import StarlightOutput

# 1. Preprocess Spectrum
wl, flx, eflx = preprocess_pipeline(
    "spectrum_raw.txt",
    z=0.015,
    av=0.3,
    reddening_law="ccm",
    rebin_step=1.0,
    output_spec_path="spectrum_clean.spec"
)

# 2. Create Mask
mask = SpectralMask.from_preset("optical")
mask.add_interval(6540.0, 6600.0, weight=0.0, name="Halpha+[NII]")
mask.save_to_file("mask_spectrum_clean.sm")

# 3. Configure and Generate Grid
config = StarlightConfig(
    base_dir="./BasesDir/",
    base_file="BaseHRpyPopStarChab",
    procs=4
)
grid_files = generate_grid_files(["spectrum_clean.spec"], config)

# 4. Parse Results
out = StarlightOutput("./synt/spectrum_clean.out")
print(f"Chi2: {out.chi2:.2f}, A_V: {out.av:.2f}, Mean log Age: {out.mean_log_age_l:.2f}")
```

---

## 🛠️ The 4-Step Workflow

### Step ① — Data Ingestion & Preprocessing
* Load spectra from `.txt`, `.dat`, `.csv`, `.spec`, or `.fits`.
* Apply Galactic dereddening ($A_V, R_V$) using standard extinction laws.
* Convert to rest-frame and rebin onto a linear grid ($\Delta\lambda$).
* Filter telluric bands and export directly to Starlight `.spec` format.

### Step ② — Spectral Masking
* Apply optical or NIR emission line presets with a single click.
* Add, edit, or delete custom masked intervals with specific weights (0.0 for masked lines, 2.0 for higher weight).
* Export and import `.sm` mask files.

### Step ③ — STARLIGHT Configuration & Grid Execution
* Set base directories, base model manifests, kinematics options, and fit ranges.
* Generate multi-core `grid_*.inp` files.
* Execute the STARLIGHT binary with real-time log streaming and progress monitoring.

### Step ④ — Results & Stellar Population Analysis
* Load and inspect STARLIGHT `.out` synthesis files.
* Interactive plots: Observed vs. Synthetic fit, residual spectrum, error bands, and masked intervals.
* Visual bar charts for light fractions ($x_j$) and mass fractions ($m_j$) across SSP age and metallicity bins.
* Export publication-quality figures (PNG/PDF) and summary tables (`.csv`).

---

## 📂 Project Structure

```
starlight-runner/
├── pyproject.toml
├── requirements.txt
├── README.md
├── StarlightChains_v04RR_25klines_1000Base.exe
├── starlight_runner/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main_gui.py           # 4-step modern PyQt5 GUI application
│   ├── custom_widgets.py     # Range sliders, collapsible cards, canvas
│   ├── preprocessing.py      # Dereddening, rest-frame, rebinning, telluric cut
│   ├── reddening.py          # CCM89, Calzetti00, Fitzpatrick99, Seaton79, Gordon24
│   ├── masking.py            # Mask management, optical & NIR line presets, .sm I/O
│   ├── runner.py             # Grid generator, config writer & subprocess runner
│   ├── parser.py             # Output .out parser, population vector diagnostics
│   └── templates/            # Default StCv04.C99.config and base definitions
```

---

*Author:* **Rogério Riffel** (riffel@ufrgs.br) — *Universidade Federal do Rio Grande do Sul (UFRGS)*
