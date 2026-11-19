"""
Example: fit one of the CSV spectra in testfiles/ with STARLIGHT using the
45-component BC03 base (Base.BC03.N, Chabrier IMF, 3 Z x 15 ages) from the
official STARLIGHT v04 distribution.

    python examples/bc03_csv/run_example.py [spectrum.csv]
    python examples/bc03_csv/run_example.py --setup   # only prepare files for the GUI

The tarball is looked for in this folder
(examples/bc03_csv/StarlightChains_v04.Distrib.tar.bz2); if it is not
there, the first run downloads StarlightChains_v04.Distrib.tar.bz2 (~5 MB) from
the STARLIGHT site and extracts only the 45 SSP spectra into ./BasesDir/.
Everything is written inside this folder:

    starlight_input/   CSV converted to STARLIGHT ASCII (.spec)
    grid_example_1.inp grid file fed to the Fortran binary
    out/               STARLIGHT output (.out)
    fit.png            observed vs. synthetic spectrum
"""

import os
import sys
import glob
import shutil
import tarfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from starlight_runner.runner import StarlightConfig, generate_grid_files, run_single_grid  # noqa: E402
from starlight_runner.parser import StarlightOutput  # noqa: E402

DISTRIB_URL = "https://minerva.ufsc.br/starlight/files/downloads/StarlightChains_v04.Distrib.tar.bz2"
DISTRIB_TAR = "StarlightChains_v04.Distrib.tar.bz2"
BASE_FILE = "Base.BC03.N"
BASE_DIR = "BasesDir"
MASK_FILE = "Masks.EmLines.SDSS.gm"
CONFIG_FILE = "StCv04.C99.config"
EXE = os.path.join(REPO, "StarlightChains_v04RR_25klines_1000Base.exe")
DEFAULT_SPEC = os.path.join(REPO, "testfiles", "IntegratedSpec_r_2.0_0.csv")


def base_components():
    """SSP file names listed in Base.BC03.N (first line = N_base)."""
    with open(BASE_FILE) as fh:
        n = int(fh.readline().split()[0])
        return [fh.readline().split()[0] for _ in range(n)]


def ensure_bases():
    """Download the distribution (once) and extract the SSPs of Base.BC03.N."""
    needed = base_components()
    missing = [f for f in needed if not os.path.exists(os.path.join(BASE_DIR, f))]
    if not missing:
        return
    if not os.path.exists(DISTRIB_TAR):
        print(f"Downloading {DISTRIB_URL} ...")
        urllib.request.urlretrieve(DISTRIB_URL, DISTRIB_TAR)
    os.makedirs(BASE_DIR, exist_ok=True)
    wanted = set(missing)
    with tarfile.open(DISTRIB_TAR, "r:bz2") as tar:
        for m in tar.getmembers():
            name = os.path.basename(m.name)
            if m.isfile() and name in wanted and "/BasesDir/" in f"/{m.name}":
                src = tar.extractfile(m)
                with open(os.path.join(BASE_DIR, name), "wb") as dst:
                    dst.write(src.read())
                wanted.discard(name)
    if wanted:
        raise RuntimeError(f"SSPs not found in the distribution: {sorted(wanted)[:5]} ...")
    print(f"Extracted {len(missing)} SSP spectra into {BASE_DIR}/")


def write_gui_masks(mask_dir="masks"):
    """
    The GUI picks the mask of each spectrum as <mask_dir>/<spectrum>.mask, so
    write one copy of the emission-line mask per CSV in testfiles/.
    """
    os.makedirs(mask_dir, exist_ok=True)
    specs = sorted(glob.glob(os.path.join(REPO, "testfiles", "*.csv")))
    for spec in specs:
        name = os.path.splitext(os.path.basename(spec))[0] + ".mask"
        shutil.copyfile(MASK_FILE, os.path.join(mask_dir, name))
    print(f"Wrote {len(specs)} mask(s) into {mask_dir}/ for the GUI")


def plot_fit(out_path, png="fit.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    res = StarlightOutput(out_path)
    sp = res.spectrum
    if sp.empty:
        return None
    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True,
                           gridspec_kw={"height_ratios": [3, 1]})
    w = sp["wavelength"] if "wavelength" in sp else sp.iloc[:, 0]
    ax[0].plot(w, sp["f_obs"], lw=0.7, color="k", label="observed")
    ax[0].plot(w, sp["f_syn"], lw=0.9, color="tab:red", label="STARLIGHT (Base.BC03.N)")
    ax[0].set_ylabel("F / F_norm")
    ax[0].legend()
    ax[1].plot(w, sp["f_obs"] - sp["f_syn"], lw=0.6, color="tab:blue")
    ax[1].axhline(0, color="k", lw=0.5)
    ax[1].set_xlabel("Wavelength (Å)")
    ax[1].set_ylabel("residual")
    fig.tight_layout()
    fig.savefig(png, dpi=120)
    return png


def main():
    args = [a for a in sys.argv[1:] if a != "--setup"]
    spec = os.path.abspath(args[0] if args else DEFAULT_SPEC)
    os.chdir(HERE)  # STARLIGHT reads config/base list from the working directory
    ensure_bases()
    if "--setup" in sys.argv:
        write_gui_masks()
        print("Ready. Launch the GUI from this folder (see README.md).")
        return

    cfg = StarlightConfig(
        starlight_exe=EXE,
        base_dir=BASE_DIR + "/",
        base_file=BASE_FILE,
        config_file=CONFIG_FILE,
        mask_dir="./",
        out_dir="out/",
        llow_sn=4730.0, lupp_sn=4780.0,       # S/N window
        olsyn_ini=3700.0, olsyn_fin=6900.0,   # fitted range (CSV covers 3700-6930 Å)
        delta_lamb=1.0,
        kinematics="FIT",
        reddening_law="CCM",
        velocity_shift=0.0, velocity_disp=150.0,
        is_err_available=0,                    # the CSVs have no error column
        is_flag_available=0,
        procs=1,
    )
    grids = generate_grid_files(
        [spec], cfg, output_dir=".", output_grid_prefix="grid_example_",
        default_mask_file=MASK_FILE, converted_dir="starlight_input",
    )
    print("Grid:", grids[0])
    print("Running STARLIGHT (a few minutes)...")
    res = run_single_grid(grids[0], starlight_exe=EXE, cwd=".")
    if res["returncode"] != 0:
        print(res["stdout"][-2000:], res["stderr"][-2000:])
        sys.exit(f"STARLIGHT failed (return code {res['returncode']})")

    out = os.path.join("out", os.path.splitext(os.path.basename(spec))[0] + ".out")
    if not os.path.exists(out):
        print(res["stdout"][-2000:])
        sys.exit(f"No output produced: {out}")

    s = StarlightOutput(out).summary_dict()
    print(f"\nResult: {os.path.join(HERE, out)}")
    for k in ("chi2", "adev", "snr", "av", "v0", "vd", "mean_log_age_l", "mean_log_age_m",
              "mean_z_l", "mean_z_m", "x_young", "x_interm", "x_old"):
        print(f"  {k:15s} {s[k]:.4g}")
    png = plot_fit(out)
    if png:
        print(f"Plot: {os.path.join(HERE, png)}")


if __name__ == "__main__":
    main()
