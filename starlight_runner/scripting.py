"""
scripting.py — GUI-free scripting API for STARLIGHT Runner, plus the
export / import of run scripts (same idea as urutau's script_export /
script_import).

A run script looks like this (``Export Script (.py)`` in the GUI writes it):

    from starlight_runner import StarlightRunner

    paths = {...}
    synthesis = {...}
    monte_carlo = {...}
    pylight = {...}
    preprocessing = {...}      # Step 1 (applied only with apply=True)
    mask_intervals = [...]     # Step 2 mask editor

    def run():
        runner = StarlightRunner(procs=4, workdir=WORKDIR)
        runner.set_preprocessing(**preprocessing)
        runner.set_mask_intervals(mask_intervals)
        runner.set_paths(**paths)
        runner.set_synthesis(**synthesis)
        runner.set_monte_carlo(**monte_carlo)
        runner.set_pylight(**pylight)
        runner.execute()

    if __name__ == "__main__":
        run()

``python run_starlight.py`` does what the GUI's Step 3 does (CSV conversion,
base check, normalization, standard mask, grids, STARLIGHT, Monte Carlo) and
writes the PyLight table of the fits.

``import_script(path)`` (``Load Script (.py)`` in the GUI) runs the script
with a recording StarlightRunner whose ``execute()`` does nothing, and
returns the GUI state it describes. Since it executes the script's own code,
only load scripts you trust (same as running ``python script.py``).
"""

import os
import glob
import json
import shutil
import pprint
from contextlib import contextmanager
from datetime import datetime

import numpy as np
import pandas as pd

from .runner import (
    StarlightConfig, generate_grid_files, run_starlight_batch, read_config_norm,
    write_config_with_norm, config_for_norm, norm_from_window, base_metallicities,
    natural_sort_key,
)
from .spectrum_io import DEFAULT_CONVERTED_DIR
from .pylight_reader import (
    starlightPars, popVectors, pylight_properties, format_pylight_value,
    default_pylight_config, migrate_fc_bins,
)

_IGNORED_EXTS = ('.mask', '.config', '.inp', '.out', '.base', '.py', '.pyc', '.sh',
                 '.md', '.png', '.pdf', '.json', '.bak')


class ScriptImportError(Exception):
    """Raised when a run script cannot be executed or configures nothing."""


@contextmanager
def _working_dir(path):
    old = os.getcwd()
    if path:
        os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def resolve_spectra(obs_dir, pattern="*.spec"):
    """Spectra to fit: a glob pattern, a single file, or <obs_dir>/<pattern>."""
    obs_dir = (obs_dir or ".").strip()
    pattern = (pattern or "*.spec").strip()
    if not pattern.startswith("*"):
        pattern = "*" + (pattern if pattern.startswith(".") else "." + pattern)
    if any(c in obs_dir for c in "*?"):
        files = glob.glob(obs_dir)
    elif os.path.isfile(obs_dir):
        files = [obs_dir]
    else:
        files = glob.glob(os.path.join(obs_dir, pattern))
    files = [f for f in files if os.path.isfile(f) and not f.endswith(_IGNORED_EXTS)]
    return sorted(files, key=natural_sort_key)


def check_bases(base_file, base_dir):
    """List of SSP files of ``base_file`` missing in ``base_dir`` (raises if the list is unreadable)."""
    if not os.path.isfile(base_file):
        raise FileNotFoundError(f"Base File not found: {base_file}")
    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"Bases Directory not found: {base_dir}")
    with open(base_file) as fh:
        lines = [l.split() for l in fh if l.strip() and not l.lstrip().startswith('#')]
    n = int(lines[0][0])
    return [t[0] for t in lines[1:n + 1] if not os.path.exists(os.path.join(base_dir, t[0]))]


class StarlightRunner:
    """
    Run STARLIGHT without the GUI, with the same options as Step 3.

    ``workdir`` is the folder paths are relative to (STARLIGHT is run there;
    default: the current directory).
    """

    def __init__(self, procs=None, workdir=None):
        self.procs = int(procs) if procs else max(1, (os.cpu_count() or 2) - 1)
        self.workdir = workdir
        self.paths = {}
        self.synthesis = {}
        self.monte_carlo = {"enabled": False}
        self.pylight = {}
        self.preprocessing = {"apply": False}
        self.mask_intervals = []
        self.loaded_files = {}
        self.execute_kwargs = None

    # ----------------------------------------------------------- configuration
    def set_paths(self, starlight_exe, obs_dir, config_file, base_dir, base_file, out_dir,
                  spec_pattern="*.spec", mask_dir="./", mask_ext=".mask", standard_mask=None):
        """
        Files and folders. ``standard_mask``: one mask file for every spectrum
        (otherwise ``<mask_dir>/<spectrum><mask_ext>``).
        """
        self.paths = dict(starlight_exe=starlight_exe, obs_dir=obs_dir, spec_pattern=spec_pattern,
                          mask_dir=mask_dir, mask_ext=mask_ext, standard_mask=standard_mask,
                          config_file=config_file, base_dir=base_dir, base_file=base_file,
                          out_dir=out_dir)

    def set_synthesis(self, fit_range, norm_window, kinematics="FIT", error_spectrum=True,
                      flag_spectrum=False, seed=33087221):
        """
        ``fit_range`` = (lambda_ini, lambda_fin); ``norm_window`` = (llow, lupp):
        normalization window = S/N window; l_norm of the bases is its mean.
        """
        self.synthesis = dict(fit_range=tuple(fit_range), norm_window=tuple(norm_window),
                              kinematics=kinematics, error_spectrum=bool(error_spectrum),
                              flag_spectrum=bool(flag_spectrum), seed=int(seed))

    def set_monte_carlo(self, enabled=False, n=100, mc_dir="mcmc", keep_spectra=False, seed=None):
        """Monte Carlo errors (needs an error spectrum): ``n`` realizations per spectrum."""
        self.monte_carlo = dict(enabled=bool(enabled), n=int(n), mc_dir=mc_dir,
                                keep_spectra=bool(keep_spectra), seed=seed)

    def set_pylight(self, config=None, galaxy_distance=0.0, table="pylight_props.csv"):
        """
        PyLight table of the fits (``table`` relative to the output folder; None
        to skip). ``config``: PyLight configuration (default: the GUI's); its
        metallicities are always taken from the Base File.
        """
        self.pylight = dict(config=config, galaxy_distance=float(galaxy_distance), table=table)

    def set_preprocessing(self, z=0.0, extinction_law="CCM (Cardelli+89 MW)", av=0.0, rv=3.1,
                          rebin_step=1.0, trim=None, telluric_cuts=None, downgrade=None, apply=False):
        """
        Step 1 settings. With ``apply=True`` every spectrum is corrected before
        the fit exactly as Step 1 does (deredden, rest frame, downgrade, trim,
        rebin, remove ``telluric_cuts``) into starlight_input/preprocessed/.
        ``trim``: (wl_min, wl_max) or None. ``telluric_cuts``: [(low, upp), ...]
        or [{'low', 'upp', 'name'}, ...]. ``downgrade``: None or
        dict(mode='R'|'sigma'|'FWHM', initial=..., target=..., initial_file=..., target_file=...).
        """
        cuts = []
        for c in telluric_cuts or []:
            if isinstance(c, dict):
                cuts.append({"low": float(c["low"]), "upp": float(c["upp"]), "name": c.get("name", "Telluric cut")})
            else:
                cuts.append({"low": float(c[0]), "upp": float(c[1]), "name": "Telluric cut"})
        self.preprocessing = dict(z=float(z), extinction_law=extinction_law, av=float(av), rv=float(rv),
                                  rebin_step=float(rebin_step), trim=tuple(trim) if trim else None,
                                  telluric_cuts=cuts, downgrade=dict(downgrade) if downgrade else None,
                                  apply=bool(apply))

    def set_mask_intervals(self, intervals=None):
        """Step 2 mask editor content: [{'low', 'upp', 'weight', 'name'}, ...] (kept for the GUI)."""
        self.mask_intervals = [dict(i) for i in (intervals or [])]

    def set_loaded_files(self, step1=None, step1_processed=False, step2=None, results=None):
        """
        Files the GUI reopens when this script is loaded (not used by execute()):
        Step 1 spectrum (and whether 'Run Preprocessing' was done), Step 2
        spectrum, Step 4 fits (.out).
        """
        self.loaded_files = dict(step1=step1, step1_processed=bool(step1_processed),
                                 step2=step2, results=list(results or []))

    def _preprocess_kwargs(self):
        pp = self.preprocessing
        dg = pp.get("downgrade")
        downgrade = None
        if dg:
            downgrade = {"mode": dg.get("mode", "R"), "val_ini": dg.get("initial"),
                         "val_target": dg.get("target"), "file_ini": dg.get("initial_file"),
                         "file_target": dg.get("target_file")}
        return dict(z=pp.get("z", 0.0), law=pp.get("extinction_law", "CCM (Cardelli+89 MW)"),
                    av=pp.get("av", 0.0), rv=pp.get("rv", 3.1), downgrade=downgrade,
                    trim=pp.get("trim"), rebin_step=pp.get("rebin_step", 1.0),
                    exclude_regions=[(c["low"], c["upp"]) for c in pp.get("telluric_cuts", [])] or None)

    @classmethod
    def from_gui_state(cls, path, workdir=None):
        """Runner configured from a GUI state (.json, 'Save Config State')."""
        with open(path) as fh:
            state = json.load(fh)
        runner = cls(workdir=workdir)
        runner.apply_state(state)
        return runner

    # ------------------------------------------------------- GUI state mapping
    def to_state(self):
        """The GUI state (Save Config State keys) described by this runner."""
        p, s, m, pl = self.paths, self.synthesis, self.monte_carlo, self.pylight
        lo, hi = s.get("norm_window", (12200.0, 12250.0))
        state = {
            "exe": p.get("starlight_exe", ""), "obs_dir": p.get("obs_dir", ""),
            "spec_ext": p.get("spec_pattern", "*.spec"),
            "mask_dir": p.get("mask_dir", "./"), "mask_ext": p.get("mask_ext", ".mask"),
            "std_mask_enabled": bool(p.get("standard_mask")),
            "std_mask_file": p.get("standard_mask") or "",
            "config_file": p.get("config_file", ""), "base_dir": p.get("base_dir", ""),
            "base_file": p.get("base_file", ""), "out_dir": p.get("out_dir", ""),
            "fit_ini": float(s.get("fit_range", (3850.0, 24000.0))[0]),
            "fit_fin": float(s.get("fit_range", (3850.0, 24000.0))[1]),
            "llow_norm": float(lo), "lupp_norm": float(hi), "l_norm": norm_from_window(lo, hi)[0],
            "sn_low": float(lo), "sn_upp": float(hi),
            "kinematics": s.get("kinematics", "FIT"), "procs": self.procs,
            "is_err_available": int(s.get("error_spectrum", True)),
            "is_flag_available": int(s.get("flag_spectrum", False)),
            "seed": int(s.get("seed", 33087221)),
            "mc_enabled": bool(m.get("enabled", False)), "mc_n": int(m.get("n", 100)),
            "mc_dir": m.get("mc_dir", "mcmc"), "mc_keep_spectra": bool(m.get("keep_spectra", False)),
            "gal_dist": float(pl.get("galaxy_distance", 0.0)),
        }
        if pl.get("config"):
            state["pylight_config"] = pl["config"]
        pp = self.preprocessing
        if len(pp) > 1:  # set_preprocessing() was called
            dg = pp.get("downgrade") or {}
            trim = pp.get("trim")
            state.update({
                "preprocessing_apply": bool(pp.get("apply", False)),
                "z": pp["z"], "law": pp["extinction_law"], "av": pp["av"], "rv": pp["rv"],
                "rebin_step": pp["rebin_step"], "telluric_cuts": pp["telluric_cuts"],
                "trim_bounds_enabled": bool(trim),
                **({"trim_min": float(trim[0]), "trim_max": float(trim[1])} if trim else {}),
                "downgrade_res_enabled": bool(dg),
                "res_mode": {"R": 0, "sigma": 1, "FWHM": 2}.get(dg.get("mode", "R"), 0),
                "res_ini_is_file": bool(dg.get("initial_file")),
                "res_ini_file_path": dg.get("initial_file") or "",
                "res_ini": float(dg.get("initial") or 5000.0),
                "res_tgt_is_file": bool(dg.get("target_file")),
                "res_tgt_file_path": dg.get("target_file") or "",
                "res_tgt": float(dg.get("target") or 2000.0),
            })
        if self.mask_intervals:
            state["masks"] = self.mask_intervals
        if self.loaded_files:
            state["loaded_files"] = dict(self.loaded_files)
        return state

    def apply_state(self, state):
        """Configure from a GUI state dict (inverse of to_state)."""
        lo = state.get("llow_norm", state.get("sn_low", 12200.0))
        hi = state.get("lupp_norm", state.get("sn_upp", 12250.0))
        self.procs = int(state.get("procs", self.procs))
        self.set_paths(
            starlight_exe=state.get("exe", ""), obs_dir=state.get("obs_dir", ""),
            spec_pattern=state.get("spec_ext", "*.spec"), mask_dir=state.get("mask_dir", "./"),
            mask_ext=state.get("mask_ext", ".mask"),
            standard_mask=state.get("std_mask_file") if state.get("std_mask_enabled") else None,
            config_file=state.get("config_file", ""), base_dir=state.get("base_dir", ""),
            base_file=state.get("base_file", ""), out_dir=state.get("out_dir", ""))
        self.set_synthesis(
            fit_range=(state.get("fit_ini", 3850.0), state.get("fit_fin", 24000.0)),
            norm_window=(lo, hi), kinematics=state.get("kinematics", "FIT"),
            error_spectrum=bool(state.get("is_err_available", 1)),
            flag_spectrum=bool(state.get("is_flag_available", 0)), seed=state.get("seed", 33087221))
        self.set_monte_carlo(
            enabled=state.get("mc_enabled", False), n=state.get("mc_n", 100),
            mc_dir=state.get("mc_dir", "mcmc"), keep_spectra=state.get("mc_keep_spectra", False))
        cfg = state.get("pylight_config")
        if cfg:
            cfg = dict(cfg)
            cfg.pop("Zs_source", None)
            migrate_fc_bins(cfg)
        self.set_pylight(config=cfg, galaxy_distance=state.get("gal_dist", 0.0))
        downgrade = None
        if state.get("downgrade_res_enabled"):
            downgrade = {
                "mode": ("R", "sigma", "FWHM")[int(state.get("res_mode", 0))],
                "initial": None if state.get("res_ini_is_file") else state.get("res_ini", 5000.0),
                "initial_file": state.get("res_ini_file_path") if state.get("res_ini_is_file") else None,
                "target": None if state.get("res_tgt_is_file") else state.get("res_tgt", 2000.0),
                "target_file": state.get("res_tgt_file_path") if state.get("res_tgt_is_file") else None,
            }
        self.set_preprocessing(
            z=state.get("z", 0.0), extinction_law=state.get("law", "CCM (Cardelli+89 MW)"),
            av=state.get("av", 0.0), rv=state.get("rv", 3.1), rebin_step=state.get("rebin_step", 1.0),
            trim=(state.get("trim_min"), state.get("trim_max")) if state.get("trim_bounds_enabled") else None,
            telluric_cuts=state.get("telluric_cuts", state.get("cuts", [])), downgrade=downgrade,
            apply=state.get("preprocessing_apply", False))
        self.set_mask_intervals(state.get("masks", []))
        self.set_loaded_files(**(state.get("loaded_files") or {}))

    # ------------------------------------------------------------- execution
    def _config(self):
        p, s = self.paths, self.synthesis
        if not p or not s:
            raise ValueError("Call set_paths() and set_synthesis() before execute().")
        lo, hi = s["norm_window"]
        return StarlightConfig(
            starlight_exe=p["starlight_exe"], obs_dir=p["obs_dir"], mask_dir=p["mask_dir"],
            mask_ext=p["mask_ext"], config_file=p["config_file"], base_dir=p["base_dir"],
            base_file=p["base_file"], out_dir=p["out_dir"],
            olsyn_ini=float(s["fit_range"][0]), olsyn_fin=float(s["fit_range"][1]),
            llow_sn=float(lo), lupp_sn=float(hi), kinematics=s["kinematics"],
            is_err_available=int(s["error_spectrum"]), is_flag_available=int(s["flag_spectrum"]),
            seed=s["seed"], procs=self.procs, data_ext=p["spec_pattern"])

    def execute(self, update_config_norm=False, log=print):
        """
        Run everything. If the normalization window differs from the .config,
        ``update_config_norm=True`` rewrites the .config (copy kept as .bak);
        otherwise a copy with it is used from starlight_input/.
        Returns a dict with the grids, outputs and tables written.
        """
        from .montecarlo import (prepare_monte_carlo, cleanup_mc_spectra, load_mc_outputs,
                                 mc_statistics, write_mc_table, error_spectrum_problem)
        self.execute_kwargs = dict(update_config_norm=update_config_norm)
        with _working_dir(self.workdir):
            cfg = self._config()
            p, m = self.paths, self.monte_carlo
            log(f"STARLIGHT Runner — {datetime.now():%Y-%m-%d %H:%M}  (working dir: {os.getcwd()})")

            specs = resolve_spectra(p["obs_dir"], p["spec_pattern"])
            if not specs:
                raise FileNotFoundError(f"No spectra matching '{p['spec_pattern']}' in '{p['obs_dir']}'.")
            log(f"{len(specs)} spectrum(a) in {p['obs_dir']} ({p['spec_pattern']})")

            if self.preprocessing.get("apply"):
                # Step 1 on every spectrum (same function as the GUI)
                from .preprocessing import preprocess_file
                pre_dir = os.path.join(DEFAULT_CONVERTED_DIR, "preprocessed")
                kw = self._preprocess_kwargs()
                new = []
                for spec in specs:
                    out = os.path.join(pre_dir, os.path.splitext(os.path.basename(spec))[0] + ".spec")
                    new.append(preprocess_file(spec, out, **kw))
                specs, cfg.obs_dir = new, pre_dir
                log(f"Step 1 applied (z={kw['z']}, {kw['law']}, A_V={kw['av']}, R_V={kw['rv']}, "
                    f"Δλ={kw['rebin_step']}) → {pre_dir}/")

            missing = check_bases(cfg.base_file, cfg.base_dir)
            if missing:
                raise FileNotFoundError(f"{len(missing)} base spectra missing in {cfg.base_dir}: {missing[:5]}")

            # normalization window (= S/N window); l_norm = its mean
            norm = norm_from_window(*self.synthesis["norm_window"])
            file_norm = read_config_norm(cfg.config_file)
            if file_norm and any(abs(a - b) > 1e-6 for a, b in zip(file_norm, norm)):
                log(f"Normalization {norm} differs from {cfg.config_file} {file_norm}")
                if update_config_norm:
                    shutil.copyfile(cfg.config_file, cfg.config_file + ".bak")
                    write_config_with_norm(cfg.config_file, cfg.config_file, *norm)
                    log(f"  → {cfg.config_file} updated (backup .bak)")
                else:
                    cfg.config_file = config_for_norm(cfg.config_file, norm, DEFAULT_CONVERTED_DIR)
                    log(f"  → using {cfg.config_file}")

            std_mask = p.get("standard_mask")
            if std_mask:
                if not os.path.isfile(std_mask):
                    raise FileNotFoundError(f"Standard mask not found: {std_mask}")
                cfg.mask_dir = os.path.dirname(std_mask) or "."
                log(f"Standard mask for all spectra: {std_mask}")

            grids = generate_grid_files(specs, cfg, default_mask_file=std_mask)
            log(f"{len(grids)} grid file(s): {', '.join(grids)}")

            jobs = []
            if m.get("enabled"):
                if not self.synthesis["error_spectrum"]:
                    raise ValueError("Monte Carlo needs an error spectrum (error_spectrum=True).")
                ext = cfg.mask_ext if cfg.mask_ext.startswith('.') else "." + cfg.mask_ext
                for spec in specs:
                    problem = error_spectrum_problem(spec)
                    if problem:
                        raise ValueError(f"Monte Carlo: {problem}")
                    mask = std_mask or os.path.join(
                        cfg.mask_dir or ".", os.path.splitext(os.path.basename(spec))[0] + ext)
                    job = prepare_monte_carlo(spec, cfg, m["n"], mask_file=mask,
                                              seed=m.get("seed"), mc_dir=m.get("mc_dir") or "mcmc")
                    jobs.append(job)
                    grids = grids + job["grids"]
                    log(f"Monte Carlo: {m['n']} realizations of {os.path.basename(spec)} → {job['root']}")

            log(f"Running STARLIGHT on {len(grids)} grid(s) with {self.procs} process(es)...")
            done = []

            def progress(res):
                done.append(res)
                status = "ok" if res["returncode"] == 0 else f"ERROR {res['returncode']}"
                log(f"  [{len(done)}/{len(grids)}] {res['grid']}: {status}")

            results = run_starlight_batch(grids, cfg.starlight_exe, cwd=".",
                                          max_workers=self.procs, progress_callback=progress)

            pyl = self.pylight
            pcfg = dict(pyl.get("config") or default_pylight_config())
            zs = base_metallicities(cfg.base_file)
            if zs:
                pcfg["Zs"] = zs  # metallicities always from the Base File
            gal_d = pyl.get("galaxy_distance", 0.0)

            tables = []
            for job in jobs:
                if not m.get("keep_spectra"):
                    cleanup_mc_spectra(job)
                outs = [o for o in job["outs"] if os.path.exists(o)]
                if len(outs) < 2:
                    log(f"Monte Carlo {job['base']}: only {len(outs)} fit(s) — no statistics.")
                    continue
                stats = mc_statistics(load_mc_outputs(outs), pcfg, gal_d)
                table = os.path.join(job["root"], f"{job['base']}_mc_props.csv")
                write_mc_table(stats, table, name=job["base"], pylight_config=pcfg)
                tables.append(table)
                log(f"Monte Carlo {job['base']}: mean ± std of {len(outs)} fits → {table}")

            outs = [os.path.join(cfg.out_dir, os.path.splitext(os.path.basename(s))[0] + ".out")
                    for s in specs]
            outs = [o for o in outs if os.path.exists(o)]
            if pyl.get("table", "pylight_props.csv") and outs:
                rows = []
                for o in outs:
                    pars, ParList, _, _, _, version = starlightPars(o)
                    pop, comps = popVectors(o)
                    props = pylight_properties(pars, ParList, pop, comps, version, pcfg, gal_d)
                    row = {"File": os.path.basename(o)}
                    row.update({k: format_pylight_value(k, v, pcfg) for k, v in props.items()})
                    rows.append(row)
                table = os.path.join(cfg.out_dir, pyl.get("table", "pylight_props.csv"))
                pd.DataFrame(rows).to_csv(table, index=False)
                tables.append(table)
                log(f"PyLight table ({len(rows)} fit(s)) → {table}")

            n_err = sum(r["returncode"] != 0 for r in results)
            log(f"Finished: {len(outs)}/{len(specs)} fit(s) in {cfg.out_dir}"
                + (f", {n_err} grid(s) with errors" if n_err else ""))
            return {"grids": grids, "outs": outs, "tables": tables, "results": results}


# ----------------------------------------------------------------------------
# Export: GUI state -> run script
# ----------------------------------------------------------------------------

def _fmt(value, indent=0, width=88):
    """Readable Python literal: dicts one key per line (nested), short values inline."""
    pad = " " * (indent + 4)
    if isinstance(value, dict) and value:
        one_line = repr(value)
        if len(one_line) + indent <= width and not any(isinstance(v, dict) for v in value.values()):
            return one_line
        items = [f"{pad}{k!r}: {_fmt(v, indent + 4, width)}," for k, v in value.items()]
        return "{\n" + "\n".join(items) + "\n" + " " * indent + "}"
    text = repr(value)
    if isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
        return "[\n" + "\n".join(f"{pad}{v!r}," for v in value) + "\n" + " " * indent + "]"
    if len(text) + indent > width and isinstance(value, (list, tuple)) and value:
        import textwrap
        open_, close = ("[", "]") if isinstance(value, list) else ("(", ")")
        body = textwrap.fill(", ".join(repr(v) for v in value) + ",", width=width,
                             initial_indent=pad, subsequent_indent=pad, break_long_words=False)
        text = open_ + "\n" + body + "\n" + " " * indent + close
    return text


def workdir_for_script(script_path, workdir=None):
    """
    How a script at ``script_path`` should find ``workdir`` (default: cwd):
    relative to the script when both share a folder tree (so they can be
    moved together), absolute otherwise.
    """
    workdir = os.path.abspath(workdir or os.getcwd())
    script_dir = os.path.dirname(os.path.abspath(script_path))
    try:
        common = os.path.commonpath([workdir, script_dir])
    except ValueError:  # different drives (Windows)
        return workdir
    if common in (os.sep, os.path.expanduser("~")) and workdir != script_dir:
        return workdir
    return os.path.relpath(workdir, script_dir)


def generate_script(state, workdir_rel="."):
    """
    Standalone .py reproducing the GUI's Step 3 run for ``state`` (GUI state
    dict). ``workdir_rel``: folder the paths are relative to, relative to the
    script's own location (so script and data can be moved together).
    """
    r = StarlightRunner()
    r.apply_state(state)
    p, s, m, pl = r.paths, r.synthesis, r.monte_carlo, r.pylight
    paths = {"starlight_exe": p["starlight_exe"], "obs_dir": p["obs_dir"],
             "spec_pattern": p["spec_pattern"], "mask_dir": p["mask_dir"], "mask_ext": p["mask_ext"],
             "standard_mask": p["standard_mask"], "config_file": p["config_file"],
             "base_dir": p["base_dir"], "base_file": p["base_file"], "out_dir": p["out_dir"]}
    synthesis = {"fit_range": s["fit_range"], "norm_window": s["norm_window"],
                 "kinematics": s["kinematics"], "error_spectrum": s["error_spectrum"],
                 "flag_spectrum": s["flag_spectrum"], "seed": s["seed"]}
    monte_carlo = {"enabled": m["enabled"], "n": m["n"], "mc_dir": m["mc_dir"],
                   "keep_spectra": m["keep_spectra"]}
    pcfg = dict(pl.get("config") or default_pylight_config())
    pcfg.pop("Zs_source", None)
    pcfg.pop("Zs", None)  # always taken from the Base File
    pylight = {"galaxy_distance": pl.get("galaxy_distance", 0.0), "table": "pylight_props.csv",
               "config": pcfg}
    pp = dict(r.preprocessing)
    preprocessing = {"apply": pp.get("apply", False), "z": pp["z"], "extinction_law": pp["extinction_law"],
                     "av": pp["av"], "rv": pp["rv"], "rebin_step": pp["rebin_step"], "trim": pp["trim"],
                     "telluric_cuts": pp["telluric_cuts"],
                     "downgrade": pp["downgrade"]}
    mask_intervals = r.mask_intervals
    lf = r.loaded_files or {}
    loaded_files = {"step1": lf.get("step1"), "step1_processed": lf.get("step1_processed", False),
                    "step2": lf.get("step2"), "results": lf.get("results", [])}

    return f'''"""
STARLIGHT Runner script — generated {datetime.now():%Y-%m-%d %H:%M}.

Runs what Step 3 of the GUI does (CSV conversion, base check, normalization,
grids, STARLIGHT, Monte Carlo) and writes the PyLight table of the fits:

    python {{this file}}

It can also be loaded back into the GUI ("Load Script (.py)").
Paths are relative to WORKDIR (by default the folder of this script).
"""
import os

from starlight_runner import StarlightRunner

WORKDIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), {workdir_rel!r}))

# ---- Files and folders (Step 3: Paths) -------------------------------------
# standard_mask: one mask file for all spectra (None: <mask_dir>/<spectrum><mask_ext>)
paths = {_fmt(paths)}

# ---- Synthesis parameters (Step 3) -----------------------------------------
# norm_window = normalization window = S/N window; l_norm of the bases = its mean
synthesis = {_fmt(synthesis)}

# ---- Monte Carlo errors (need an error spectrum) ---------------------------
monte_carlo = {_fmt(monte_carlo)}

# ---- Step 1: preprocessing ---------------------------------------------------
# apply=False: only kept as the GUI's Step 1 settings (spectra are fitted as they are).
# apply=True : every spectrum is corrected as in Step 1 (deredden, rest frame,
#              downgrade, trim, rebin, remove telluric_cuts) before the fit.
# trim: (lambda_min, lambda_max) or None; telluric_cuts: regions removed after rebinning;
# downgrade: None or
#       {{'mode': 'R'|'sigma'|'FWHM', 'initial': ..., 'target': ..., 'initial_file': None, 'target_file': None}}
preprocessing = {_fmt(preprocessing)}

# ---- Step 2: mask editor intervals (kept for the GUI; the fit uses the mask files) --
mask_intervals = {_fmt(mask_intervals)}

# ---- Files reopened in the GUI when this script is loaded (not used by run()) --
# step1: spectrum of Step 1 (step1_processed: 'Run Preprocessing' was done),
# step2: spectrum of Step 2, results: fits (.out) shown in Step 4
loaded_files = {_fmt(loaded_files)}

# ---- PyLight table (written in the output folder) --------------------------
# metallicities (Zs) are always the unique Z of the Base File
pylight = {_fmt(pylight)}

PROCS = {r.procs}


def run():
    runner = StarlightRunner(procs=PROCS, workdir=WORKDIR)
    runner.set_preprocessing(**preprocessing)
    runner.set_mask_intervals(mask_intervals)
    runner.set_loaded_files(**loaded_files)
    runner.set_paths(**paths)
    runner.set_synthesis(**synthesis)
    runner.set_monte_carlo(**monte_carlo)
    runner.set_pylight(**pylight)
    # update_config_norm=True rewrites the .config when its normalization differs
    # (backup .bak); False uses a copy from starlight_input/
    runner.execute(update_config_norm=False)


if __name__ == "__main__":
    run()
'''


# ----------------------------------------------------------------------------
# Import: run script -> GUI state
# ----------------------------------------------------------------------------

class _RecordingRunner(StarlightRunner):
    """StarlightRunner stand-in used while importing a script: execute() only records."""
    _last = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _RecordingRunner._last = self

    def execute(self, update_config_norm=False, log=print):
        self.execute_kwargs = dict(update_config_norm=update_config_norm)


def import_script(path, gui_cwd=None):
    """
    Run a script with a recording StarlightRunner and return (state, warnings):
    the GUI state it configures, with paths made relative to ``gui_cwd``
    (default: current directory). Executes the script's code: trusted scripts only.
    """
    import starlight_runner as pkg
    from . import scripting as mod

    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    real_pkg, real_mod = pkg.StarlightRunner, mod.StarlightRunner
    pkg.StarlightRunner = mod.StarlightRunner = _RecordingRunner
    _RecordingRunner._last = None
    old_cwd = os.getcwd()
    try:
        ns = {"__name__": "__main__", "__file__": os.path.abspath(path)}
        try:
            exec(compile(source, path, "exec"), ns)
        except Exception as e:
            raise ScriptImportError(f"Error while running '{os.path.basename(path)}': {e}") from e
    finally:
        pkg.StarlightRunner, mod.StarlightRunner = real_pkg, real_mod
        os.chdir(old_cwd)

    rec = _RecordingRunner._last
    if rec is None or not rec.paths:
        raise ScriptImportError("The script never created a StarlightRunner with set_paths() — nothing to import.")

    warnings = []
    if not rec.synthesis:
        warnings.append("set_synthesis() was not called — synthesis parameters left at defaults.")
    if rec.execute_kwargs is None:
        warnings.append("The script never called runner.execute().")

    # paths relative to the script's WORKDIR -> relative to the GUI's working dir
    gui_cwd = os.path.abspath(gui_cwd or os.getcwd())
    base = os.path.abspath(rec.workdir) if rec.workdir else gui_cwd
    if base != gui_cwd:
        def rebase(v):
            if not v or os.path.isabs(v):
                return v
            rel = os.path.relpath(os.path.join(base, v), gui_cwd)
            return rel + ("/" if v.endswith("/") and not rel.endswith("/") else "")
        for k in ("starlight_exe", "obs_dir", "mask_dir", "standard_mask", "config_file",
                  "base_dir", "base_file", "out_dir"):
            rec.paths[k] = rebase(rec.paths.get(k))
        rec.monte_carlo["mc_dir"] = rebase(rec.monte_carlo.get("mc_dir"))
        lf = rec.loaded_files or {}
        for k in ("step1", "step2"):
            if lf.get(k):
                lf[k] = rebase(lf[k])
        if lf.get("results"):
            lf["results"] = [rebase(f) for f in lf["results"]]
        warnings.append(f"Paths were relative to {base}; converted to the GUI's folder {gui_cwd}.")
    return rec.to_state(), warnings


def main(argv=None):
    """``python -m starlight_runner.scripting state.json [-o run.py]``: GUI state → run script."""
    import argparse
    ap = argparse.ArgumentParser(description="Write a STARLIGHT Runner script from a GUI state (.json).")
    ap.add_argument("state", help="GUI state saved with 'Save Config State'")
    ap.add_argument("-o", "--output", default="run_starlight.py", help="script to write (default run_starlight.py)")
    args = ap.parse_args(argv)
    with open(args.state) as fh:
        state = json.load(fh)
    rel = workdir_for_script(args.output)
    with open(args.output, "w") as fh:
        fh.write(generate_script(state, workdir_rel=rel))
    print(f"Script written: {args.output} (paths relative to {os.getcwd()})")


if __name__ == "__main__":
    main()
