# Example: CSV spectrum + Base.BC03.N (45 SSPs)

Fits `testfiles/IntegratedSpec_r_2.0_0.csv` (columns `wavelength,flux_mean`,
3700–6930 Å, no error column) with STARLIGHT using the 45-component BC03 base
from the official STARLIGHT v04 distribution
(<http://www.starlight.ufsc.br/downloads/>): Chabrier IMF, 3 metallicities
(Z = 0.004, 0.02, 0.05) × 15 ages (1 Myr – 13 Gyr).

## Where to put the tarball

The base spectra are **not** in git. They come from the official STARLIGHT
distribution, which must sit **inside this folder** with its original name:

```
starlight-runner/
├── StarlightChains_v04RR_25klines_1000Base.exe      ← binary used by the example
├── testfiles/IntegratedSpec_r_2.0_*.csv             ← spectra to fit
└── examples/bc03_csv/
    ├── StarlightChains_v04.Distrib.tar.bz2          ← PUT THE TARBALL HERE
    ├── BasesDir/                                    ← created: the 45 SSPs of Base.BC03.N
    ├── Base.BC03.N
    ├── StCv04.C99.config
    ├── Masks.EmLines.SDSS.gm
    └── run_example.py
```

- **With internet:** do nothing. If the tarball is missing, `run_example.py`
  downloads it from
  <https://minerva.ufsc.br/starlight/files/downloads/StarlightChains_v04.Distrib.tar.bz2>
  (~5 MB, linked from <http://www.starlight.ufsc.br/downloads/>).
- **Offline / manual:** download it yourself and copy it to
  `examples/bc03_csv/StarlightChains_v04.Distrib.tar.bz2` (do not unpack it).

On every run the script checks `BasesDir/` and extracts from the tarball only
the 45 SSP files listed in `Base.BC03.N` that are missing. Once `BasesDir/`
is complete the tarball can be deleted.

## Running from the command line

```bash
python examples/bc03_csv/run_example.py                 # default spectrum
python examples/bc03_csv/run_example.py testfiles/IntegratedSpec_r_2.0_3.csv
```

| File | Origin / role |
|---|---|
| `Base.BC03.N` | base list (45 SSPs), from the distribution |
| `StCv04.C99.config` | distribution config (normalization 4010–4060 Å), `i_verbose_anneal = 0` |
| `Masks.EmLines.SDSS.gm` | emission-line mask from the distribution, used for every spectrum |
| `run_example.py` | converts the CSV, writes the grid, runs the 64-bit binary of the repo, prints the results and saves `fit.png` |

Setup used in the grid: S/N window 4730–4780 Å, fit 3700–6900 Å,
Δλ = 1 Å, CCM extinction, kinematics fitted (v0 = 0, σ = 150 km/s initial),
`IsErrSpecAvailable = 0` because the CSVs have no errors.

Outputs (ignored by git): `starlight_input/` (CSV → `.spec`),
`grid_example_1.inp`, `out/<spectrum>.out`, `fit.png`.

The 32-bit `StarlightChains_v04.exe` of the distribution is not used; the
example runs `StarlightChains_v04RR_25klines_1000Base.exe` (64-bit static)
from the repository root, which reads the same config/base formats.

## Loading the example in the GUI (fitter)

STARLIGHT reads the configuration file and the base list (`Base.BC03.N`) from
the **working directory**, so the GUI must be started from this folder.

1. Prepare the bases and one mask per spectrum (the GUI looks for
   `<mask dir>/<spectrum>.mask`):

   ```bash
   python examples/bc03_csv/run_example.py --setup
   ```

   This uses/downloads the tarball as above, fills `BasesDir/` and writes
   `masks/IntegratedSpec_r_2.0_*.mask` (copies of `Masks.EmLines.SDSS.gm`).

2. Start the GUI from this folder:

   ```bash
   cd examples/bc03_csv
   python -m starlight_runner        # package installed (pip install -e .)
   # or, without installing:  PYTHONPATH=../.. python -m starlight_runner
   ```

3. In **Step 3 (STARLIGHT Grid)** fill in:

   | Field | Value |
   |---|---|
   | Starlight Binary | `../../StarlightChains_v04RR_25klines_1000Base.exe` |
   | Obs Spectra Dir | `../../testfiles` |
   | Spectrum Extension / Pattern | `*.csv` |
   | Masks Directory | `masks/` |
   | Mask Extension | `.mask` |
   | Configuration File | `StCv04.C99.config` |
   | Bases Directory | `BasesDir/` |
   | Base File | `Base.BC03.N` |
   | Output Directory | `out/` |
   | Fit λ Lower / Upper (Å) | `3700` / `6900` |
   | S/N Window Lower / Upper (Å) | `4730` / `4780` |
   | Error Spectrum | **unchecked** (the CSVs have no error column) |
   | Flag Spectrum | unchecked |

4. **Generate Grid Files** → **Run STARLIGHT**. The CSVs are converted
   automatically to `starlight_input/*.spec`; the fits go to `out/` and can
   be opened in the Results step.

