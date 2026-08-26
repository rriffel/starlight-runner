# STARLIGHT-Runner

A modern, high-performance workflow suite and graphical interface for the **STARLIGHT** Stellar Population Synthesis code.

**STARLIGHT-Runner** provides an integrated 4-step scientific pipeline from raw observed spectra to publication-ready stellar population analysis and diagnostics (PyLight).

---

## 🚀 Key Features

* **Complete 4-Step Scientific Pipeline:**
  1. **Preprocessing & Telluric Cutting:** Galactic dereddening, rest-frame transformation, uniform linear rebinning ($\Delta\lambda$), and interactive telluric / boundary trimming.
  2. **Interactive Spectral Masking (CreateMasks Mode):** Full-screen interactive masking studio with 2-point point-and-click masking, weight controls ($0.0$ for excluded regions, $2.0$ for key features), and optical/NIR presets.
  3. **Multi-core Grid Generation & Parallel Execution:** Automated batch grid generation (`grid_*.inp`), base library validation, and multi-process STARLIGHT execution with live diagnostics console and progress tracking.
  4. **PyLight Results & Stellar Population Explorer:** Multi-panel visualization of best-fit synthetic spectra, residuals ($O - S$), age/metallicity population decompositions ($\Sigma x_j$, $\Sigma \mu_j$), and AGN feature analysis.
* **Extinction Laws:** Cardelli, Clayton, & Mathis (1989), Calzetti et al. (2000), Fitzpatrick (1999), Seaton (1979), and Gordon et al. (2024 SMC).
* **Self-Contained & Production-Ready:** Fully modular architecture with both an interactive GUI and a scriptable Python API.

---

## 📦 Installation

### 1. From Git Repository
Clone the repository and install in editable mode:

```bash
git clone https://github.com/rriffel/starlight-runner.git
cd starlight-runner
pip install -e .
```

### 2. Dependencies
Requires Python $\ge$ 3.8 and standard scientific packages:

```bash
pip install -r requirements.txt
```

*Required packages: `numpy`, `scipy`, `pandas`, `matplotlib`, `PyQt5`.*

---

## 🖥️ Graphical User Interface (GUI)

Launch the application directly from the terminal:

```bash
starlight-runner
```
or
```bash
python -m starlight_runner
```

---

## 🛠️ Step-by-Step Workflow Guide

### Step ① — Data Ingestion & Preprocessing
1. **Load Spectrum:** Supports `.txt`, `.dat`, `.csv`, `.spec`, and `.fits` formats.
2. **Physical Corrections:**
   - **Redshift ($z$):** Corrects wavelengths to the rest frame: $\lambda_{\text{rest}} = \lambda_{\text{obs}} / (1 + z)$.
   - **Extinction ($A_V, R_V$):** Applies dereddening using CCM89, Calzetti00, Fitzpatrick99, Seaton79, or Gordon24.
   - **Rebinning ($\Delta\lambda$):** Rebins fluxes and propagates errors onto a uniform integer or fractional linear grid (e.g. $\Delta\lambda = 1.0\text{ \AA}$) with automated deduplication.
3. **Telluric & Boundary Trimming:**
   - **Interactive Cutting:** Click directly on the plot or open the *Detached Cut Window (Full Screen)* to trim telluric bands or extreme boundaries.
   - **NIR Preset:** One-click application of standard NIR telluric water vapor bands ($1.34 - 1.42\ \mu\text{m}$ and $1.80 - 1.90\ \mu\text{m}$).
4. **Export:** Save cleaned `.spec` file and advance to Step 2.

---

### Step ② — Interactive Spectral Masking (CreateMasks Studio)
1. **Interactive Masking on Canvas:**
   - **Right-Click:** 1st and 2nd click masks region with **Weight 0.0** (Red / Excluded from fit).
   - **Middle-Click:** 1st and 2nd click masks region with **Weight 2.0** (Green / Key diagnostic feature).
   - **Key `d`:** Hover over any masked band and press `d` to immediately remove it.
   - **Key `q` / `Esc`:** Finish editing / cancel current selection.
2. **Detached Full-Screen Studio:** Pop out a dedicated full-screen window for ultra-precise masking across wide spectral ranges.
3. **Standard Presets:**
   - **Optical Preset:** Masks prominent nebular emission lines ([O II], [O III], H$\beta$, H$\alpha$, [N II], [S II], etc.).
   - **NIR Preset:** Masks near-infrared emission lines and sky absorption artifacts.
4. **File Persistence:** Seamlessly load, save, and auto-sync `.mask` files.

---

### Step ③ — STARLIGHT Grid Generator & Parallel Execution
1. **Configuration:**
   - Select the STARLIGHT binary (`starlight_stuff/StarlightChains_v04RR_25klines_1000Base.exe`).
   - Choose observed spectra directory (e.g. `testfiles/`), mask directory, `.config` file (`starlight_stuff/StCv04.C99.config`), base library directory, and base manifest file (`starlight_stuff/BasesXSLKrupaPCRR`).
2. **Batch Grid Generation:** Automatically matches all spectrum files against corresponding masks and creates `grid_*.inp` files.
3. **Base Library Verification:** Validates that all SSP FITS/text files referenced in the base manifest exist before launching.
4. **Parallel Execution:**
   - Multi-process worker pool utilizing all available CPU cores.
   - Real-time log console streaming STARLIGHT output per grid.
   - Progress bar with cancel/stop capabilities.

---

### Step ④ — Results & Stellar Population Explorer (PyLight)
1. **Load Results:** Open any STARLIGHT synthesis output (`.out`) file (supports V4 and V5).
2. **Comprehensive Multi-panel Plotting:**
   - **Observed vs. Synthetic Spectrum:** Full spectral fit comparison with masked regions highlighted.
   - **Residuals ($O - S$):** Detailed residual spectrum with zero-line reference.
   - **Summed Stellar Populations:** Light fractions ($\Sigma x_j$) and mass fractions ($\Sigma \mu_j$) grouped by SSP age.
   - **Decomposition by Metallicity:** Population vectors separated by metallicity ($Z / Z_\odot$).
   - **Binned Population Vectors:** Young ($t \le 100\text{ Myr}$), Intermediate ($100\text{ Myr} < t \le 2\text{ Gyr}$), and Old ($t > 2\text{ Gyr}$).
   - **AGN Components:** Visual analysis of featureless continuum (FC) power-law index $\alpha$ and hot dust (BB) temperature bins.
3. **Pylight Configuration Editor:** Dynamically adjust metallicity display lists, $Z_\odot$, age bin intervals, and AGN component toggles.
4. **Export:**
   - High-resolution publication figures (**PNG**, **PDF**, **SVG**).
   - Parameter tables (**CSV**, **TXT**).

---

## 🐍 Python Scripting API

You can also use `starlight-runner` as a standalone Python library in scripts and Jupyter Notebooks:

```python
from starlight_runner.preprocessing import preprocess_pipeline
from starlight_runner.masking import SpectralMask
from starlight_runner.runner import StarlightConfig, generate_grid_files
from starlight_runner.parser import StarlightOutput

# 1. Preprocess & Rebin Raw Spectrum
wl, flx, eflx = preprocess_pipeline(
    "testfiles/comb_major_6.txt",
    z=0.015,
    av=0.3,
    reddening_law="ccm",
    rebin_step=1.0,
    output_spec_path="testfiles/comb_major_6_clean.spec"
)

# 2. Build Spectral Mask
mask = SpectralMask.from_preset("optical")
mask.add_interval(6540.0, 6600.0, weight=0.0, name="Halpha+[NII]")
mask.save_to_file("testfiles/comb_major_6_clean.mask")

# 3. Configure and Generate STARLIGHT Grids
config = StarlightConfig(
    starlight_exe="starlight_stuff/StarlightChains_v04RR_25klines_1000Base.exe",
    base_file="starlight_stuff/BasesXSLKrupaPCRR",
    config_file="starlight_stuff/StCv04.C99.config",
    obs_dir="./testfiles/",
    mask_dir="./testfiles/",
    procs=4
)
grid_files = generate_grid_files(["testfiles/comb_major_6_clean.spec"], config)

# 4. Parse Synthesis Results
out = StarlightOutput("./synt/comb_major_6_clean.out")
print(f"Chi2/N_eff: {out.chi2:.2f}")
print(f"adev: {out.adev:.2f}%")
print(f"A_V: {out.av:.2f} mag")
print(f"Mean log(Age)_L: {out.mean_log_age_l:.2f} yr")
print(f"Mean Z_L: {out.mean_z_l:.4f}")
```

---

## 📂 Repository Structure

```
starlight-runner/
├── pyproject.toml                                # Package build specification (PEP 517/518)
├── requirements.txt                              # Core dependencies
├── README.md                                     # Project documentation
├── .gitignore                                    # Git exclusion rules
├── starlight_stuff/                              # Auxiliary STARLIGHT & PyLight files
│   ├── StarlightChains_v04RR_25klines_1000Base.exe   # STARLIGHT binary (Linux x86_64)
│   ├── StCv04.C99.config                             # STARLIGHT default configuration template
│   ├── BasesXSLKrupaPCRR                             # Base manifest example (XSL / Kroupa)
│   ├── ConfigPylight                                 # PyLight plotting configuration
│   └── ConfigToStarlight                             # STARLIGHT grid configuration mapping
├── testfiles/                                    # Example test spectra & masks
│   └── comb_major_6.txt                              # Sample observed galaxy spectrum
├── tests/                                        # Automated unit tests
│   └── test_all.py
└── starlight_runner/                             # Core Python package
    ├── __init__.py
    ├── __main__.py                               # Package entrypoint (python -m starlight_runner)
    ├── main_gui.py                               # 4-step modern PyQt5 GUI application
    ├── custom_widgets.py                         # Detached studios, range widgets, plot canvases
    ├── preprocessing.py                          # Dereddening, rest-frame, linear rebinning
    ├── reddening.py                              # Extinction laws (CCM89, Calzetti00, etc.)
    ├── masking.py                                # SpectralMask manager, optical & NIR line presets
    ├── runner.py                                 # Grid generator & multi-core worker manager
    ├── parser.py                                 # StarlightOutput parser & DataFrame exporter
    ├── pylight_reader.py                         # PyLight output reader for parameters & populations
    ├── gui/                                      # GUI modular mixins
    │   ├── preprocessing_mixin.py                # Step 1: Preprocessing UI & interactive cut
    │   ├── masking_mixin.py                      # Step 2: Masking UI & CreateMasks mode
    │   ├── grid_mixin.py                         # Step 3: Grid generator & execution UI
    │   ├── results_mixin.py                      # Step 4: PyLight results & export UI
    │   ├── config_mixin.py                       # Global settings & JSON persistence
    │   └── constants.py                          # Theme tokens, styles, colors
    └── templates/                                # Built-in default configuration templates
```

---

## 👥 Authors & Scientific Citation

* **Rogério Riffel** (riffel@ufrgs.br) — *Universidade Federal do Rio Grande do Sul (UFRGS), Departamento de Astronomia.*
* **STARLIGHT** was developed by *Roberto Cid Fernandes and the SEAGal collaboration* (Cid Fernandes et al. 2005, MNRAS, 358, 363).

If you use this tool in your research, please cite the appropriate STARLIGHT and PyLight methodology papers.

---
## 📄 License
This project is licensed under the **MIT License**.
