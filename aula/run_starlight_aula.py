"""
STARLIGHT Runner script — generated 2026-11-19 17:12.

Runs what Step 3 of the GUI does (CSV conversion, base check, normalization,
grids, STARLIGHT, Monte Carlo) and writes the PyLight table of the fits:

    python {this file}

It can also be loaded back into the GUI ("Load Script (.py)").
Paths are relative to WORKDIR (by default the folder of this script).
"""
import os

from starlight_runner import StarlightRunner

WORKDIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.'))

# ---- Files and folders (Step 3: Paths) -------------------------------------
# standard_mask: one mask file for all spectra (None: <mask_dir>/<spectrum><mask_ext>)
paths = {
    'starlight_exe': 'StarlightChains_v04RR_25klines_1000Base.exe',
    'obs_dir': 'prepross',
    'spec_pattern': '.spec',
    'mask_dir': 'mask',
    'mask_ext': '.mask',
    'standard_mask': None,
    'config_file': 'StCv04.C99.config',
    'base_dir': './BasesDir/',
    'base_file': 'Base.BC03.N',
    'out_dir': './synt/',
}

# ---- Synthesis parameters (Step 3) -----------------------------------------
# norm_window = normalization window = S/N window; l_norm of the bases = its mean
synthesis = {
    'fit_range': (3750.0, 6880.0),
    'norm_window': (5650.0, 5750.0),
    'kinematics': 'FIT',
    'error_spectrum': False,
    'flag_spectrum': False,
    'seed': 33087221,
}

# ---- Monte Carlo errors (need an error spectrum) ---------------------------
monte_carlo = {'enabled': False, 'n': 100, 'mc_dir': './mcmc', 'keep_spectra': False}

# ---- Step 1: preprocessing ---------------------------------------------------
# apply=False: only kept as the GUI's Step 1 settings (spectra are fitted as they are).
# apply=True : every spectrum is corrected as in Step 1 (deredden, rest frame,
#              downgrade, trim, rebin, remove telluric_cuts) before the fit.
# trim: (lambda_min, lambda_max) or None; telluric_cuts: regions removed after rebinning;
# downgrade: None or
#       {'mode': 'R'|'sigma'|'FWHM', 'initial': ..., 'target': ..., 'initial_file': None, 'target_file': None}
preprocessing = {
    'apply': False,
    'z': 0.0,
    'extinction_law': 'CCM (Cardelli+89 MW)',
    'av': 0.033,
    'rv': 3.1,
    'rebin_step': 1.0,
    'trim': None,
    'telluric_cuts': [],
    'downgrade': None,
}

# ---- Step 2: mask editor intervals (kept for the GUI; the fit uses the mask files) --
mask_intervals = [
    {'low': 3710.0, 'upp': 3744.0, 'weight': 0.0, 'name': '[O II] 3726, 3729'},
    {'low': 3858.0, 'upp': 3880.0, 'weight': 0.0, 'name': '[Ne III] 3869'},
    {'low': 3880.0, 'upp': 3905.0, 'weight': 0.0, 'name': 'H8 + He I 3889'},
    {'low': 3960.0, 'upp': 3980.0, 'weight': 0.0, 'name': 'Hepsilon 3970 + [Ne III]'},
    {'low': 4092.0, 'upp': 4112.0, 'weight': 0.0, 'name': 'Hdelta 4102'},
    {'low': 4330.0, 'upp': 4375.0, 'weight': 0.0, 'name': 'Hgamma 4340 + [O III] 4363'},
    {'low': 4675.0, 'upp': 4700.0, 'weight': 0.0, 'name': 'He II 4686'},
    {'low': 4848.0, 'upp': 4874.0, 'weight': 0.0, 'name': 'Hbeta 4861'},
    {'low': 4940.0, 'upp': 5028.0, 'weight': 0.0, 'name': '[O III] 4959, 5007'},
    {'low': 5190.0, 'upp': 5210.0, 'weight': 0.0, 'name': '[N I] 5198, 5200'},
    {'low': 5866.0, 'upp': 5916.0, 'weight': 0.0, 'name': 'He I 5876 + Na I D'},
    {'low': 6280.0, 'upp': 6375.0, 'weight': 0.0, 'name': '[O I] 6300, 6364'},
    {'low': 6528.0, 'upp': 6608.0, 'weight': 0.0, 'name': '[N II] + Halpha + [N II] (6548, 6563, 6583)'},
    {'low': 6696.0, 'upp': 6752.0, 'weight': 0.0, 'name': '[S II] 6716, 6731'},
]

# ---- Files reopened in the GUI when this script is loaded (not used by run()) --
# step1: spectrum of Step 1 (step1_processed: 'Run Preprocessing' was done),
# step2: spectrum of Step 2, results: fits (.out) shown in Step 4
loaded_files = {'step1': None, 'step1_processed': False, 'step2': None, 'results': []}

# ---- PyLight table (written in the output folder) --------------------------
# metallicities (Zs) are always the unique Z of the Base File
pylight = {
    'galaxy_distance': 0.0,
    'table': 'pylight_props.csv',
    'config': {
        'IsAGNComp': False,
        'OnlyFC': False,
        'pltmask': False,
        'NormFac': 1,
        'SaveDist': True,
        'zsun': 0.0152,
        'BinPopVecLab': ['xy', 'xiy', 'xio', 'xo'],
        'BinPopVecMassLab': ['my', 'miy', 'mio', 'mo'],
        'BinPopVec': {
            'xy': [1000.0, 100000000.0],
            'xiy': [101000000.0, 700000000.0],
            'xio': [750000000.0, 2000000000.0],
            'xo': [2100000000.0, 15000000000.0],
        },
        'BinSFRLabs': [
            'SFR_1E6', 'SFR_5E6', 'SFR_10E6', 'SFR_14E6', 'SFR_20E6', 'SFR_30E6',
            'SFR_56E6', 'SFR_100E6', 'SFR_200E6',
        ],
        'BinSFR': {
            'SFR_1E6': [10, 1001000.0],
            'SFR_5E6': [10, 5621000.0],
            'SFR_10E6': [10, 10001000.0],
            'SFR_14E6': [10, 14100100.0],
            'SFR_20E6': [10, 20001000.0],
            'SFR_30E6': [10, 31600100.0],
            'SFR_56E6': [10, 56201000.0],
            'SFR_100E6': [10, 100001000.0],
            'SFR_200E6': [10, 200001000.0],
        },
        'BinHDVecLab': ['BB_c', 'BB_h', 'HDTot'],
        'BinHDVec': {'BB_c': [0, 1000], 'BB_h': [1000, 1500], 'HDTot': [0, 1500]},
        'BinFCVecLab': ['FC0.25', 'FC0.50', 'FC0.75', 'FCTot'],
        'BinFCVec': {
            'FC0.25': [0.0, 0.25],
            'FC0.50': [0.25, 0.5],
            'FC0.75': [0.5, 0.75],
            'FCTot': [0.0, 0.75],
        },
    },
}

PROCS = 1


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
