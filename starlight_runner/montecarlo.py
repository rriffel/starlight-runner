"""
montecarlo.py — Monte Carlo uncertainties for STARLIGHT fits.

For a given galaxy spectrum, N synthetic realizations are created by
perturbing each flux point with a Gaussian of width equal to its error
(f_sim = N(f_obs, err)). All realizations are fitted with exactly the same
STARLIGHT setup (config, base, mask, kinematics, ...) and every pylight
quantity is then reported as np.mean of the N fits with np.std of the N fits
as its error.

All products of a galaxy live in ``<mc_dir>/<galaxy>/`` (default ./mcmc):
``spec/`` (the N perturbed spectra, removed after the run unless
``keep_spectra``), ``out/`` (the N fits), the ``mc_grid_*.inp`` files and the
``<galaxy>_mc_props.csv`` table.

Typical scripted use:

    from starlight_runner import StarlightConfig
    from starlight_runner.montecarlo import run_monte_carlo, mc_statistics, write_mc_table

    cfg = StarlightConfig(base_dir=..., mask_dir="mask_dir/", ...)
    outs = run_monte_carlo("testfiles/gal.txt", cfg, n_sim=100,
                           mask_file="mask_dir/gal.mask", seed=42, mc_dir="mcmc")
    mc = load_mc_outputs(outs)
    stats = mc_statistics(mc, pylight_config, gal_dist=10.0)
    write_mc_table(stats, "gal_mc_props.csv", name="gal")

or from the command line (see ``python -m starlight_runner.montecarlo -h``).
"""

import os
import re
import copy
import glob
import shutil
import warnings

import numpy as np
import pandas as pd

from .runner import generate_grid_files, run_starlight_batch, natural_sort_key
from .pylight_reader import (
    starlightPars, popVectors, StSyntesis, pylight_properties, format_pylight_value
)

MC_TAG = "_mc"
DEFAULT_MC_DIR = "mcmc"


# ---------------------------------------------------------------------------
# 1. Synthetic spectra
# ---------------------------------------------------------------------------

def mc_paths(spec_path, mc_dir=DEFAULT_MC_DIR):
    """Galaxy name and its Monte Carlo folders: root, spec/ (realizations) and out/ (fits)."""
    base = os.path.splitext(os.path.basename(spec_path))[0]
    root = os.path.join(mc_dir or DEFAULT_MC_DIR, base)
    return {'base': base, 'root': root,
            'spec': os.path.join(root, "spec"), 'out': os.path.join(root, "out")}


def make_mc_spectra(spec_path, n_sim, out_dir=None, seed=None):
    """
    Create ``n_sim`` perturbed copies of a STARLIGHT input spectrum.

    The input is a whitespace table with columns lambda, flux, error
    (and optionally flag). Each realization keeps lambda, error and flag and
    draws flux ~ N(flux, error); points with error <= 0 are left unperturbed.

    Returns the sorted list of written files ``<base>_mc0001<ext>``, ...
    (in ``out_dir``, default ``./mcmc/<base>/spec``).
    """
    if n_sim < 1:
        raise ValueError("n_sim must be >= 1")
    data = np.loadtxt(spec_path, comments='#', ndmin=2)
    if data.shape[1] < 3:
        raise ValueError(
            f"{spec_path}: Monte Carlo needs an error column (lambda flux error [flag]); "
            f"found {data.shape[1]} column(s)."
        )
    n_bad = int(np.sum(~np.isfinite(data[:, :3]).all(axis=1)))
    if n_bad:
        # NaN/inf make STARLIGHT's chi2 undefined and the chains never converge (the fit hangs)
        raise ValueError(
            f"{spec_path}: {n_bad} point(s) with NaN/inf in lambda, flux or error. "
            "Clean the spectrum first (Step 1 / preprocessing.clean_spectrum)."
        )

    paths = mc_paths(spec_path)
    base = paths['base']
    ext = os.path.splitext(spec_path)[1] or ".spec"
    if out_dir is None:
        out_dir = paths['spec']
    os.makedirs(out_dir, exist_ok=True)

    lam, flx, eflx = data[:, 0], data[:, 1], data[:, 2]
    sigma = np.where(eflx > 0, eflx, 0.0)
    rng = np.random.default_rng(seed)
    fmt = ['%.6f', '%.8e', '%.8e'] + ['%d'] * (data.shape[1] - 3)

    width = max(4, len(str(n_sim)))
    files = []
    for i in range(1, n_sim + 1):
        sim = data.copy()
        sim[:, 1] = rng.normal(flx, sigma)
        path = os.path.join(out_dir, f"{base}{MC_TAG}{i:0{width}d}{ext}")
        np.savetxt(path, sim, fmt=fmt)
        files.append(path)
    return files


# ---------------------------------------------------------------------------
# 2. Grids & execution
# ---------------------------------------------------------------------------

def mc_config(config, mc_spec_dir, mask_file=None, out_dir=None):
    """
    Copy of a StarlightConfig pointing to the MC spectra (obs_dir), a
    dedicated output folder and, if given, the galaxy's mask folder.
    Everything else (base, config file, kinematics, windows...) is unchanged.
    """
    cfg = copy.deepcopy(config)
    cfg.obs_dir = mc_spec_dir
    if mask_file:
        cfg.mask_dir = os.path.dirname(mask_file) or "."
    if out_dir:
        cfg.out_dir = out_dir
    return cfg


def generate_mc_grids(mc_specs, config, mask_file=None, grid_dir=".", grid_prefix=None):
    """
    Write grid files for the MC spectra. If ``mask_file`` is given all
    realizations share that mask; otherwise the usual
    ``<spectrum><mask_ext>`` rule of STARLIGHT-Runner applies.
    """
    if grid_prefix is None:
        base = re.sub(rf"{MC_TAG}\d+$", "", os.path.splitext(os.path.basename(mc_specs[0]))[0])
        grid_prefix = f"mc_grid_{base}_"  # not matched by the normal grid_*.inp glob
    return generate_grid_files(
        mc_specs, config, output_dir=grid_dir,
        output_grid_prefix=grid_prefix, default_mask_file=mask_file
    )


def prepare_monte_carlo(spec_path, config, n_sim, mask_file=None, seed=None, mc_dir=DEFAULT_MC_DIR):
    """
    Create the MC spectra and grid files of one galaxy in ``<mc_dir>/<galaxy>/``
    without running STARLIGHT (the GUI runs them with its own worker thread).

    Returns a job dict: base, root, spec_dir, out_dir, grids, outs (expected
    .out files) and config (the StarlightConfig used for the realizations).
    """
    paths = mc_paths(spec_path, mc_dir)
    if mask_file and not os.path.exists(mask_file):
        raise FileNotFoundError(f"Mask file not found: {mask_file}")
    specs = make_mc_spectra(spec_path, n_sim, out_dir=paths['spec'], seed=seed)
    cfg = mc_config(config, paths['spec'], mask_file, paths['out'])
    grids = generate_mc_grids(specs, cfg, mask_file=mask_file, grid_dir=paths['root'])
    outs = [os.path.join(paths['out'], os.path.splitext(os.path.basename(s))[0] + ".out")
            for s in specs]
    return {'base': paths['base'], 'root': paths['root'], 'spec_dir': paths['spec'],
            'out_dir': paths['out'], 'grids': grids, 'outs': outs, 'config': cfg}


def cleanup_mc_spectra(job):
    """Remove the perturbed spectra (and their grid files) of a job; the fits are kept."""
    shutil.rmtree(job['spec_dir'], ignore_errors=True)
    for g in job['grids']:
        if os.path.exists(g):
            os.remove(g)


def run_monte_carlo(spec_path, config, n_sim, mask_file=None, seed=None, mc_dir=DEFAULT_MC_DIR,
                    keep_spectra=False, max_workers=None, progress_callback=None):
    """
    Full Monte Carlo run: create ``n_sim`` realizations of ``spec_path`` in
    ``<mc_dir>/<galaxy>/``, fit them all with ``config`` and return the list of
    .out files produced. Unless ``keep_spectra``, the perturbed spectra are
    removed afterwards.
    """
    job = prepare_monte_carlo(spec_path, config, n_sim, mask_file=mask_file, seed=seed, mc_dir=mc_dir)
    try:
        results = run_starlight_batch(
            job['grids'], starlight_exe=config.starlight_exe, cwd=".",
            max_workers=max_workers or config.procs, progress_callback=progress_callback
        )
    finally:
        if not keep_spectra:
            cleanup_mc_spectra(job)
    done = [o for o in job['outs'] if os.path.exists(o)]
    if not done:
        tail = "\n".join((results[0].get("stdout") or results[0].get("stderr") or "").splitlines()[-15:]) if results else ""
        raise RuntimeError(
            "STARLIGHT produced no output for the Monte Carlo realizations "
            f"(expected in '{job['out_dir']}'). Check base_dir/base_file/config paths.\n{tail}"
        )
    return done


# ---------------------------------------------------------------------------
# 3. Reading & statistics
# ---------------------------------------------------------------------------

def find_mc_outputs(out_dir, base=None):
    """List the MC .out files in ``out_dir`` (optionally of one galaxy)."""
    pattern = f"{base}{MC_TAG}*.out" if base else f"*{MC_TAG}*.out"
    return sorted(glob.glob(os.path.join(out_dir, pattern)), key=natural_sort_key)


def load_mc_outputs(out_files):
    """
    Read a set of STARLIGHT fits of the same galaxy / base.

    Returns a dict with per-run lists: 'pars', 'ParList', 'pop' and 'spec'
    (synthetic-spectrum tables) plus shared 'popComps', 'version', 'files'.
    Files that cannot be read, or whose base differs from the first one,
    are skipped and listed in 'skipped'.
    """
    runs = {'pars': [], 'pop': [], 'spec': [], 'files': [], 'skipped': []}
    ref = None
    for f in sorted(out_files, key=natural_sort_key):
        try:
            pars, ParList, _, _, _, version = starlightPars(f)
            pop, popComps = popVectors(f)
            spec = StSyntesis(f)
        except Exception as exc:
            runs['skipped'].append((f, str(exc)))
            continue
        if len(pop) == 0 or np.ndim(spec) != 2 or len(spec) == 0:
            runs['skipped'].append((f, "empty population vector or spectrum"))
            continue
        if ref is None:
            ref = dict(ParList=ParList, popComps=popComps, version=version,
                       n_base=len(pop), n_lam=len(spec))
        elif len(pop) != ref['n_base'] or len(spec) != ref['n_lam']:
            runs['skipped'].append((f, "different base or wavelength grid"))
            continue
        runs['pars'].append(pars)
        runs['pop'].append(pop)
        runs['spec'].append(spec)
        runs['files'].append(f)
    if ref is None:
        raise ValueError("None of the selected .out files could be read.")
    runs.update(ref)
    runs['n'] = len(runs['files'])
    return runs


def mean_and_std(values, axis=0):
    """
    NaN-aware np.mean and np.std (the error) of the N realizations along
    ``axis``. Returns (mean, std, n).
    """
    values = np.asarray(values, dtype=float)
    n = np.sum(np.isfinite(values), axis=axis)
    with warnings.catch_warnings(), np.errstate(invalid='ignore', divide='ignore'):
        warnings.simplefilter('ignore', RuntimeWarning)  # all-NaN columns (e.g. masses without distance)
        mean = np.nanmean(values, axis=axis) if values.size else np.nan
        std = np.nanstd(values, axis=axis) if values.size else np.nan
    return mean, std, n


def _get_par(pars, ParList, name):
    for i, p in enumerate(ParList):
        if name in p and i < len(pars):
            return pars[i]
    return np.nan


def mc_property_table(mc, pylight_config, gal_dist=0.0):
    """One row per realization with all pylight quantities (+ v0, vd)."""
    rows = []
    for f, pars, pop in zip(mc['files'], mc['pars'], mc['pop']):
        props = pylight_properties(pars, mc['ParList'], pop, mc['popComps'],
                                   mc['version'], pylight_config, gal_dist)
        props['v0'] = _get_par(pars, mc['ParList'], 'v0_min')
        props['vd'] = _get_par(pars, mc['ParList'], 'vd_min')
        rows.append({'File': os.path.basename(f), **props})
    return pd.DataFrame(rows)


def mc_statistics(mc, pylight_config, gal_dist=0.0):
    """
    Mean and error (std of the N fits) of every pylight quantity.

    Returns a DataFrame indexed by property with columns mean, std and N.
    """
    table = mc_property_table(mc, pylight_config, gal_dist)
    props = table.drop(columns=['File'])
    mean, std, n = mean_and_std(props.to_numpy(dtype=float), axis=0)
    return pd.DataFrame({'mean': mean, 'std': std, 'N': n}, index=props.columns)


def write_mc_table(stats, path, name="", pylight_config=None):
    """
    Save a one-row pylight-style table: for each property ``p`` the columns
    ``p`` (mean) and ``std_p`` (error = std of the N fits).
    """
    row = {'File': name, 'N_sim': int(stats['N'].max()) if len(stats) else 0}
    for p, r in stats.iterrows():
        row[p] = format_pylight_value(p, r['mean'], pylight_config)
        row[f'std_{p}'] = format_pylight_value(p, r['std'], pylight_config)
    df = pd.DataFrame([row])
    if path.endswith('.txt') or path.endswith('.dat'):
        df.to_csv(path, sep='\t', index=False)
    else:
        df.to_csv(path, index=False)
    return df


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def _config_from_gui_state(path):
    """Build a StarlightConfig from a STARLIGHT-Runner GUI state (.json)."""
    import json
    from .runner import StarlightConfig
    with open(path) as fh:
        st = json.load(fh)
    keymap = {
        "exe": "starlight_exe", "obs_dir": "obs_dir", "mask_dir": "mask_dir",
        "mask_ext": "mask_ext", "config_file": "config_file", "base_dir": "base_dir",
        "base_file": "base_file", "out_dir": "out_dir", "fit_ini": "olsyn_ini",
        "fit_fin": "olsyn_fin", "sn_low": "llow_sn", "sn_upp": "lupp_sn",
        "kinematics": "kinematics", "procs": "procs", "seed": "seed",
        "is_err_available": "is_err_available", "is_flag_available": "is_flag_available",
    }
    kwargs = {v: st[k] for k, v in keymap.items() if k in st and st[k] not in ("", None)}
    return StarlightConfig(**kwargs), st.get("pylight_config", {})


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(
        description="Monte Carlo uncertainties for a STARLIGHT fit: perturb the spectrum "
                    "N times within its errors, fit all realizations with the same setup "
                    "and report the mean and std of every property."
    )
    ap.add_argument("spectrum", help="observed spectrum (lambda flux error [flag])")
    ap.add_argument("-n", "--nsim", type=int, default=100, help="number of realizations (default 100)")
    ap.add_argument("--state", required=True, help="GUI configuration state (.json) with the STARLIGHT setup")
    ap.add_argument("--mask", help="mask file used for all realizations (default: <mask_dir>/<spectrum><mask_ext>)")
    ap.add_argument("--seed", type=int, help="random seed for the realizations")
    ap.add_argument("--dist", type=float, default=0.0, help="galaxy distance in Mpc (V4 masses/SFR)")
    ap.add_argument("--mc-dir", default=DEFAULT_MC_DIR, help="directory for the simulations (default ./mcmc)")
    ap.add_argument("--keep-spectra", action="store_true", help="keep the perturbed spectra (removed by default)")
    ap.add_argument("--table", help="output table (default <mc-dir>/<spectrum>/<spectrum>_mc_props.csv)")
    ap.add_argument("--no-run", action="store_true", help="only aggregate existing MC .out files")
    args = ap.parse_args(argv)

    config, pyl_cfg = _config_from_gui_state(args.state)
    paths = mc_paths(args.spectrum, args.mc_dir)
    base = paths['base']
    mask = args.mask
    if mask is None:
        ext = config.mask_ext if config.mask_ext.startswith('.') else f".{config.mask_ext}"
        cand = os.path.join(config.mask_dir, base + ext)
        mask = cand if os.path.exists(cand) else None

    if args.no_run:
        outs = find_mc_outputs(paths['out'], base)
    else:
        outs = run_monte_carlo(args.spectrum, config, args.nsim, mask_file=mask, seed=args.seed,
                               mc_dir=args.mc_dir, keep_spectra=args.keep_spectra,
                               progress_callback=lambda r: print(f"  {r['grid']}: exit {r['returncode']}"))
    mc = load_mc_outputs(outs)
    stats = mc_statistics(mc, pyl_cfg, gal_dist=args.dist)
    table = args.table or os.path.join(paths['root'], f"{base}_mc_props.csv")
    write_mc_table(stats, table, name=base, pylight_config=pyl_cfg)
    with pd.option_context('display.max_rows', None, 'display.float_format', '{:.4g}'.format):
        print(stats)
    print(f"\n{mc['n']} realizations aggregated -> {table}")


if __name__ == "__main__":
    main()
