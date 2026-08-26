"""
runner.py — STARLIGHT execution engine and grid manager.
Handles configuration files, grid file generation, multi-core batch partitioning,
and local subprocess execution of the STARLIGHT Fortran binary.
"""

import os
import re
import sys
import subprocess
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path


DEFAULT_CONFIG_TEMPLATE = """# Configuration parameters for StarlightChains_v04.for
#
# Normalization lambdas
12225.0        [l_norm    (A)]                  = for base spectra only
12200.0        [llow_norm (A)]                  = for observed spectrum
12250.0        [lupp_norm (A)]                  =  "   "        "    
#
# Parameter Limits
   -1.0        [AV_low (mag)]                   = lower allowed AV
    5.0        [AV_upp (mag)]                   = upper allowed AV
   -0.001      [YAV_low (mag)]                  = lower allowed YAV
    0.001      [YAV_upp (mag)]                  = upper allowed YAV
    0.7        [fn_low]                         = lower allowed Norm. factor = sum x_j
    1.3        [fn_upp]                         = upper allowed Norm. factor = sum x_j
 -500.0        [v0_low (km/s)]                  = lower allowed v0
  500.0        [v0_upp (km/s)]                  = upper allowed v0
    0.0        [vd_low (km/s)]                  = lower allowed vd
  500.0        [vd_upp (km/s)]                  = upper allowed vd
#
# Clipping options & Weight-Control-Filter
NSIGMA         [clip_method_option]             = NOCLIP/NSIGMA/RELRES/ABSRES = possible clipping methods
3.0            [sig_clip_threshold]             = clip points which deviate > than this # of sigmas
2.0            [wei_nsig_threshold]             = weight-control-filter. Use <= 0 to turn this off!
#
# Miscellaneous
   40.0        [dl_cushion (A)]                 = safety margin for kinematical filter!
    0.0001     [f_cut (units of f_norm)]        = Mask/ignore very low fluxes: f_obs <= f_cut
   41          [N_int_Gauss]                    = # of points for integration of kinematical filter 
    1          [i_verbose]                      = 0/1      = Quiet/Talkative
    1          [i_verbose_anneal]               = 0/1/2/3  = Quiet/.../Verborragic
    0          [Is1stLineHeader]                = 1/0 = Y/N
    0          [i_FastBC03_FLAG]                = 1 for Fast-rebin of BC03 spectra!
    0          [i_FitPowerLaw]                  = 1/0 = Y/N - include a Power Law in base 
   -0.5        [alpha_PowerLaw]                 = PL index, only used if iFitPowerLaw = 1
    0          [i_SkipExistingOutFiles]         = 1/0 = Y/N - skip or overwrite fits with already existent arq_out
#
# Markov Chains technical parameters
   12          [N_chains]                       = # of Markov Chains
    0.50       [xinit_max]                      = max(x_j) for initial random chain pop-vecs
    0          [i_UpdateEps]                    = 1/0 = Y/N. Not well tested: use 0!
    2          [i_UpdateAlpha]                  = 0/1/2. 1 & 2 update step-sizes dynamically. 0 turns this off.
    2.0        [Falpha]                         = step-updating-factor.
    1          [i_MoveOneParOnly]               = 1/0 = Y/N. Not tested/debugged! Use 1!
    1          [i_UpdateAVYAVStepSeparately]    = 1/0 = Y/N. 
    1          [i_HelpParWithMaxR]              = 1/0 = Y/N. Help convergence of ParWithMaxR 
    0.2        [prob_jRmax]                     = prob to pick ParWithMaxR
    1          [i_HelpPopVectorMove2Average]    = 1/0 = Y/N. Help x convergence 
    0.4        [prob_HelpPopVectorMove2Average] = prob of inverting sign of x-move to go towards mean
    1          [i_HelpAVYAVMove2Average]        = 1/0 = Y/N. Help AV/YAV convergence 
    0.4        [prob_HelpAVYAVMove2Average]     = prob of inverting sign of AV/YAV-move to go towards mean
"""


class StarlightConfig:
    """
    Configuration manager for Starlight synthesis runs.
    """

    def __init__(self, **kwargs):
        self.starlight_exe = kwargs.get("starlight_exe", "StarlightChains_v04RR_25klines_1000Base.exe")
        self.base_dir = kwargs.get("base_dir", "./BasesDir/")
        self.obs_dir = kwargs.get("obs_dir", "./")
        self.mask_dir = kwargs.get("mask_dir", "./")
        self.mask_ext = kwargs.get("mask_ext", ".mask")
        self.out_dir = kwargs.get("out_dir", "./synt/")

        self.config_file = kwargs.get("config_file", "StCv04.C99.config")
        self.base_file = kwargs.get("base_file", "BasesFile")
        self.reddening_law = kwargs.get("reddening_law", "CCM")
        self.velocity_shift = kwargs.get("velocity_shift", 0.0)
        self.velocity_disp = kwargs.get("velocity_disp", 150.0)
        self.seed = kwargs.get("seed", 33087221)
        self.llow_sn = kwargs.get("llow_sn", 12200.0)
        self.lupp_sn = kwargs.get("lupp_sn", 12250.0)
        self.olsyn_ini = kwargs.get("olsyn_ini", 3850.0)
        self.olsyn_fin = kwargs.get("olsyn_fin", 24000.0)
        self.delta_lamb = kwargs.get("delta_lamb", 1.0)
        self.fscale_chi2 = kwargs.get("fscale_chi2", 1.0)
        self.kinematics = kwargs.get("kinematics", "FIT")
        self.is_err_available = kwargs.get("is_err_available", 1)
        self.is_flag_available = kwargs.get("is_flag_available", 0)
        self.procs = kwargs.get("procs", max(1, multiprocessing.cpu_count() - 1))
        self.data_ext = kwargs.get("data_ext", ".spec")

    def to_dict(self):
        return vars(self).copy()

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


def natural_sort_key(s):
    """Human sort key helper."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]


def _to_rel_dir(d):
    if not d or d.strip() in (".", "./"):
        return "./"
    d = d.strip()
    try:
        rel = os.path.relpath(d, ".")
        if not rel.startswith(".."):
            d = rel
    except Exception:
        pass
    if not d.endswith(('/', '\\')):
        d += '/'
    return d


def generate_grid_files(spec_files, config, output_dir=".", output_grid_prefix="grid_", default_mask_file=None):

    """
    Generate STARLIGHT grid input files (e.g. grid_1.inp, grid_2.inp, ...)
    partitioning the list of spectra across the specified number of processors.
    Paths in headers are written relative to current working directory.
    
    Returns:
        list of generated grid file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(config.out_dir, exist_ok=True)
    
    sorted_files = sorted(spec_files, key=natural_sort_key)
    n_files = len(sorted_files)
    if n_files == 0:
        raise ValueError("No spectrum files provided for grid generation.")

    n_procs = min(config.procs, n_files)
    chunk_size = n_files // n_procs
    remainder = n_files % n_procs
    
    generated_grids = []
    start_idx = 0

    b_dir = _to_rel_dir(config.base_dir)
    o_dir = _to_rel_dir(config.obs_dir)
    m_dir = _to_rel_dir(config.mask_dir)
    s_dir = _to_rel_dir(config.out_dir)

    def _pad(val, comment, min_width=40):
        s_val = str(val)
        # Ensure at least 4 spaces
        spaces = max(4, min_width - len(s_val))
        return f"{s_val}{' ' * spaces}{comment}\n"

    for p in range(1, n_procs + 1):
        # Distribute remainder evenly across first few chunks
        current_chunk = chunk_size + (1 if p <= remainder else 0)
        end_idx = start_idx + current_chunk
        chunk_files = sorted_files[start_idx:end_idx]
        start_idx = end_idx

        grid_filepath = os.path.join(output_dir, f"{output_grid_prefix}{p}.inp")

        with open(grid_filepath, 'w') as f:
            f.write(f"{len(chunk_files)}\n")
            f.write(_pad(b_dir, "[base_dir]"))
            f.write(_pad(o_dir, "[obs_dir]"))
            f.write(_pad(m_dir, "[mask_dir]"))
            f.write(_pad(s_dir, "[out_dir]"))
            f.write(_pad(config.seed, "[your phone number]"))
            f.write(_pad(f"{config.llow_sn:.1f}", "[llow_SN]   lower-lambda of S/N window"))
            f.write(_pad(f"{config.lupp_sn:.1f}", "[lupp_SN]   upper-lambda of S/N window"))
            f.write(_pad(f"{config.olsyn_ini:.1f}", "[Olsyn_ini] lower-lambda for fit"))
            f.write(_pad(f"{config.olsyn_fin:.1f}", "[Olsyn_fin] upper-lambda for fit"))
            f.write(_pad(f"{config.delta_lamb:.1f}", "[Odlsyn]    delta-lambda for fit"))
            f.write(_pad(f"{config.fscale_chi2:.1f}", "[fscale_chi2] fudge-factor for chi2"))
            f.write(_pad(config.kinematics, "[FIT/FXK] Fit or Fix kinematics"))
            f.write(_pad(config.is_err_available, "[IsErrSpecAvailable]  1/0 = Yes/No"))
            f.write(_pad(config.is_flag_available, "[IsFlagSpecAvailable] 1/0 = Yes/No"))

            for spec in chunk_files:
                spec_name = os.path.basename(spec)
                base_name = os.path.splitext(spec_name)[0]
                spec_dir = os.path.dirname(spec)

                mask_ext = config.mask_ext if config.mask_ext.startswith('.') else f".{config.mask_ext}"
                mask_name = f"{base_name}{mask_ext}"

                out_name = f"{base_name}.out"
                config_name = os.path.basename(config.config_file)
                base_file_name = os.path.basename(config.base_file)

                line = (
                    f"{spec_name} {config_name} {base_file_name} {mask_name} "
                    f"{config.reddening_law} {config.velocity_shift:.1f} "
                    f"{config.velocity_disp:.1f} {out_name}\n"
                )
                f.write(line)

        generated_grids.append(grid_filepath)

    return generated_grids



def run_single_grid(grid_filepath, starlight_exe="StarlightChains_v04RR_25klines_1000Base.exe", cwd="."):
    """
    Run STARLIGHT Fortran binary on a single grid file.
    Executes: `./starlight_exe < grid_filepath`
    """
    exe_path = os.path.abspath(os.path.join(cwd, starlight_exe)) if not os.path.isabs(starlight_exe) else starlight_exe
    if not os.path.exists(exe_path):
        # Look in workspace or path
        exe_path = starlight_exe

    with open(grid_filepath, 'r') as grid_in:
        process = subprocess.Popen(
            [exe_path],
            stdin=grid_in,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True
        )
        stdout, stderr = process.communicate()
        return {
            "grid": grid_filepath,
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr
        }


def run_starlight_batch(
    grid_files,
    starlight_exe="StarlightChains_v04RR_25klines_1000Base.exe",
    cwd=".",
    max_workers=None,
    progress_callback=None
):
    """
    Execute multiple grid files in parallel using ProcessPoolExecutor.
    """
    max_workers = max_workers or min(len(grid_files), os.cpu_count() or 1)
    results = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_grid = {
            executor.submit(run_single_grid, g, starlight_exe, cwd): g
            for g in grid_files
        }
        for future in as_completed(future_to_grid):
            grid = future_to_grid[future]
            try:
                res = future.result()
                results.append(res)
                if progress_callback:
                    progress_callback(res)
            except Exception as exc:
                err_res = {"grid": grid, "returncode": -1, "stdout": "", "stderr": str(exc)}
                results.append(err_res)
                if progress_callback:
                    progress_callback(err_res)

    return results
