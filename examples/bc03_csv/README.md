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
| `StCv04.C99.config` | distribution config (normalization window 4010–4060 Å), `i_verbose_anneal = 0` and `l_norm = 4035` (mean of the window; the distribution has 4020) |
| `Masks.EmLines.SDSS.gm` | emission-line mask from the distribution, used for every spectrum |
| `run_example.py` | converts the CSV, writes the grid, runs the 64-bit binary of the repo, prints the results and saves `fit.png` |

Setup used in the grid: normalization (= S/N) window 4010–4060 Å with
l_norm = 4035 Å (its mean), fit 3700–6900 Å,
Δλ = 1 Å, CCM extinction, kinematics fitted (v0 = 0, σ = 150 km/s initial),
`IsErrSpecAvailable = 0` because the CSVs have no errors.

Outputs (ignored by git): `starlight_input/` (CSV → `.spec`),
`grid_example_1.inp`, `out/<spectrum>.out`, `fit.png`.

The 32-bit `StarlightChains_v04.exe` of the distribution is not used; the
example runs `StarlightChains_v04RR_25klines_1000Base.exe` (64-bit static)
from the repository root, which reads the same config/base formats.

## Loading the example in the GUI (fitter)

`starlight_gui_config_bc03.json` is a ready GUI state for this example. All
its paths are relative to the **repository root**, so start the GUI there.

1. Once, prepare the bases (uses or downloads the tarball, see above):

   ```bash
   python examples/bc03_csv/run_example.py --setup
   ```

   This fills `examples/bc03_csv/BasesDir/` with the 45 SSPs. The masks the
   GUI needs (`masks/<spectrum>.mask`, one per CSV in `testfiles/`) are
   already in git and are rewritten by `--setup`.

2. From the repository root start the GUI and load the state:

   ```bash
   python -m starlight_runner
   ```

   **Load Config** → `examples/bc03_csv/starlight_gui_config_bc03.json`

3. Step 3 → **Run STARLIGHT** (answer *Yes* to regenerate the grids). The 8
   CSVs are converted to `starlight_input/*.spec`, the fits go to
   `examples/bc03_csv/out/` and can be opened in the Results step.

What the state sets:

| Field | Value |
|---|---|
| Starlight Binary | `StarlightChains_v04RR_25klines_1000Base.exe` |
| Obs Spectra Dir / Pattern | `testfiles` / `*.csv` |
| Masks Directory / Extension | `examples/bc03_csv/masks` / `.mask` |
| Configuration File | `examples/bc03_csv/StCv04.C99.config` |
| Bases Directory / Base File | `examples/bc03_csv/BasesDir` / `examples/bc03_csv/Base.BC03.N` |
| Output Directory | `examples/bc03_csv/out` |
| Fit λ (Å) | 3700–6900 |
| Norm Window (= S/N window) / Norm λ for Bases (Å) | 4010–4060 / 4035 (mean) |
| Error / Flag spectrum | off / off (the CSVs have no error column) |
| Masking step (Step 2) | the 11 emission-line windows of `Masks.EmLines.SDSS.gm` |
| PyLight | BC03 metallicities Z = 0.004, 0.02, 0.05; Z☉ = 0.02; no AGN component |

The configuration file and base list live in this folder; the grid writes
them as quoted paths (`'examples/bc03_csv/StCv04.C99.config'`), because
STARLIGHT reads the grid line list-directed and an unquoted `/` would end it.
