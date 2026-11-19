"""
pylight_reader.py — Standalone parser for STARLIGHT output files for PyLight plotting.
Extracts fit parameters, population vectors, and synthetic spectrum tables.
"""

import os
import glob
import numpy as np


def starlightPars(filename):
    """
    Extract scalar fit parameters from STARLIGHT V4 / V5 output files.
    Returns: pars, ParList, popin, popend, syntin, version
    """
    cnt = 1
    pars = np.zeros(0)
    popin = 0
    popend = 0
    syntin = 0
    version = 'V4'
    ParList = []

    with open(filename, 'r') as Table:
        filecont = Table.readlines()

    if len(filecont) < 2:
        return pars, ParList, popin, popend, syntin, version

    if 'PANcMExStarlight' in filecont[1]:
        version = 'V5'
        ParList = [
            '[chi2/Nl_eff', 'chi2]', 'flux_unit]', 'fobs_norm', 'Lobs_norm', 'LumDistInMpc',
            '[adev (%)]', '[Lum_tot (Lsun/A if distance & flux_unit are Ok...)]',
            '[Mini_tot (Msun  if distance & flux_unit are Ok...)]',
            '[Mcor_tot (Msun  if distance & flux_unit are Ok...)]',
            '[AV_min  (mag)]', '[sum-of-x (%)]', '[l_norm (A) - for base]',
            '[llow_norm (A) - window for f_obs]', '[lupp_norm (A) - window for f_obs]',
            '[v0_min  (km/s)]', '[S/N in S/N window]', '[N_base]', '[sum-of-x (%)]', '[vd_min  (km/s)]'
        ]
        for par in ParList:
            for line in filecont:
                if par in line:
                    tline = line.split()
                    if par == 'chi2]':
                        parm = float(tline[1])
                        pars = np.append(pars, parm)
                    elif par == 'flux_unit]':
                        parm = float(tline[1])
                        pars = np.append(pars, parm)
                    elif par == 'Lobs_norm':
                        parm = float(tline[1])
                        pars = np.append(pars, parm)
                    elif par == 'LumDistInMpc':
                        parm = float(tline[2])
                        pars = np.append(pars, parm)
                    else:
                        parm = float(tline[0])
                        pars = np.append(pars, parm)

        for line in filecont:
            if 'x_j(%)' in line:
                popin = cnt
            if '## Synthesis Results' in line:
                popend = cnt - 2
            if '## Synthetic spectrum (Best Model) ##l_obs f_obs f_syn wei' in line:
                syntin = cnt + 1
            cnt += 1

    else:
        version = 'V4'
        ParList = [
            '[chi2/Nl_eff]', '[fobs_norm (in input units)]', '[adev (%)]',
            '[Flux_tot (units of input spectrum!)]', '[Mini_tot (???)]', '[Mcor_tot (???)]',
            '[AV_min  (mag)]', '[YAV_min (mag)]', '[sum-of-x (%)]', '[l_norm (A) - for base]',
            '[llow_norm (A) - window for f_obs]', '[lupp_norm (A) - window for f_obs]',
            '[v0_min  (km/s)]', '[S/N in S/N window]', '[N_base]', '[sum-of-x (%)]', '[vd_min  (km/s)]'
        ]
        for par in ParList:
            for line in filecont:
                if par in line:
                    tline = line.split()
                    parm = float(tline[0])
                    pars = np.append(pars, parm)
        for line in filecont:
            if 'x_j(%)' in line:
                popin = cnt
            if '## Synthesis Results' in line:
                popend = cnt - 2
            if '## Synthetic spectrum (Best Model) ##l_obs f_obs f_syn wei' in line:
                syntin = cnt + 1
            cnt += 1

    return pars, ParList, popin, popend, syntin, version


def popVectors(filein):
    """
    Load population vectors from STARLIGHT output file.
    Returns:
      pop: np.ndarray with columns [x_j(%), Mini_j(%), Mcor_j(%), age_j(yr), Z_j, (L/M)_j, j]
      popComps: np.ndarray of component label strings
    """
    x = starlightPars(filein)
    linebeg = int(x[2])
    linefin = int(x[3])
    with open(filein, 'r') as tmp:
        tmpcont = tmp.readlines()
    tempcut = tmpcont[linebeg:linefin]

    pop_list = []
    comps_list = []
    for line in tempcut:
        tokens = line.strip().split()
        if len(tokens) >= 7:
            try:
                j = float(tokens[0])
                x_j = float(tokens[1])
                mini_j = float(tokens[2])
                mcor_j = float(tokens[3])
                age_j = float(tokens[4])
                z_j = float(tokens[5])
                lm_j = float(tokens[6])
                pop_list.append([x_j, mini_j, mcor_j, age_j, z_j, lm_j, j])
                # columns: j x_j Mini_j Mcor_j age_j Z_j (L/M)_j YAV? Mstars component_j a/Fe ...
                comp = tokens[9] if len(tokens) > 9 else (tokens[-1] if len(tokens) > 7 else f"ssp_{int(j)}")
                comps_list.append(comp)
            except ValueError:
                continue

    pop = np.array(pop_list) if pop_list else np.empty((0, 7))
    popComps = np.array(comps_list) if comps_list else np.array([])
    return pop, popComps


def StSyntesis(filein):
    """
    Load synthetic spectrum table (l_obs, f_obs, f_syn, wei).
    """
    x = starlightPars(filein)
    skip = int(x[4])
    try:
        spec = np.genfromtxt(filein, skiprows=skip, missing_values='*', filling_values='-1.00')
    except Exception:
        spec = np.genfromtxt(filein, skip_header=skip, missing_values='*', filling_values='-1.00')
    return spec


# Keys formatted in scientific notation / with 4 significant figures in pylight tables
_SCI_KEYS = ('M*', 'M*in', 'F_Norm')
_Z_KEYS = ('MZ_L', 'MZ_M')


def format_pylight_value(key, value, config=None):
    """Format a pylight quantity following the original pylight.py conventions."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 'NaN'
    sfr_keys = (config or {}).get('BinSFRLabs', [])
    if key in _SCI_KEYS or key in sfr_keys or key.startswith('SFR_'):
        return f'{value:.2E}'
    if key in _Z_KEYS:
        return f'{value:.4}'
    return f'{value:.2f}'


def _get_par(pars, ParList, name):
    for i, p in enumerate(ParList):
        if name in p and i < len(pars):
            return pars[i]
    return np.nan


# AGN components (same nomenclature and rules as urutau's starlight wrapper):
#   featureless continuum  agn_fc_<alpha>   (alpha = 0.25, 0.5, 0.75)
#   hot dust black body    agn_bb_<T in K>
# Stellar populations exclude every component whose name starts with one of
# _AGN_PREFIXES (legacy BB_/Power_/PL_ names included).
_AGN_PREFIXES = ("agn_bb", "bb", "agn_fc", "power", "pl_")

# Default FC bins for the agn_fc_<alpha> nomenclature, (min, max] in alpha
DEFAULT_FC_BINS_LAB = ['FC0.25', 'FC0.50', 'FC0.75', 'FCTot']
DEFAULT_FC_BINS = {'FC0.25': [0.0, 0.25], 'FC0.50': [0.25, 0.50], 'FC0.75': [0.50, 0.75], 'FCTot': [0.0, 0.75]}
_LEGACY_FC_BINS_LAB = ['FC1.25', 'FC1.50', 'FC1.75', 'FCTot']


def default_pylight_config():
    """Default PyLight configuration (GUI and scripting API). Zs are replaced by the Base File's."""
    return {
        'Zs': [0.00382, 0.00959, 0.0152, 0.02409],
        'IsAGNComp': False,  # AGN components (FC, hot dust) off by default
        'OnlyFC': False,
        'pltmask': False,
        'NormFac': 1,
        'SaveDist': True,
        'zsun': 0.0152,
        'BinPopVecLab': ['xy', 'xiy', 'xio', 'xo'],
        'BinPopVecMassLab': ['my', 'miy', 'mio', 'mo'],
        'BinPopVec': {'xy': [1E3, 100e6], 'xiy': [101e6, 700e6], 'xio': [750E6, 2E9], 'xo': [2.10e9, 15e9]},
        'BinSFRLabs': ['SFR_1E6', 'SFR_5E6', 'SFR_10E6', 'SFR_14E6', 'SFR_20E6', 'SFR_30E6', 'SFR_56E6', 'SFR_100E6', 'SFR_200E6'],
        'BinSFR': {"SFR_1E6": [10,1.001E6], "SFR_5E6": [10,5.621E6], "SFR_10E6": [10,10.001E6],"SFR_14E6":[10,14.1001E6],"SFR_20E6": [10,20.001E6],"SFR_30E6": [10,31.6001E6],"SFR_56E6": [10,56.201E6],"SFR_100E6":[10,100.001E6],"SFR_200E6": [10,200.001E6]},
        'BinHDVecLab': ['BB_c', 'BB_h', 'HDTot'],
        'BinHDVec': {'BB_c': [0, 1000], 'BB_h': [1000, 1500], 'HDTot': [0, 1500]},
        # FC bins in alpha of the agn_fc_<alpha> components (0.25, 0.5, 0.75), (min, max]
        'BinFCVecLab': ['FC0.25', 'FC0.50', 'FC0.75', 'FCTot'],
        'BinFCVec': {'FC0.25': [0.0, 0.25], 'FC0.50': [0.25, 0.50], 'FC0.75': [0.50, 0.75], 'FCTot': [0.0, 0.75]}
    }


def is_agn_component(comp):
    """True for AGN components (featureless continuum or hot-dust black body)."""
    return str(comp).strip().lower().startswith(_AGN_PREFIXES)


def agn_fc_exponent(comp):
    """alpha of an ``agn_fc_<alpha>`` component, else None."""
    c = str(comp).strip().lower()
    if not c.startswith("agn_fc_"):
        return None
    try:
        return float(c[len("agn_fc_"):])
    except ValueError:
        return None


def agn_bb_temperature(comp):
    """T (K) of an ``agn_bb_<T>`` component, else None."""
    c = str(comp).strip().lower()
    if not c.startswith("agn_bb_"):
        return None
    try:
        return float(c[len("agn_bb_"):])
    except ValueError:
        return None


def migrate_fc_bins(config):
    """
    Replace the legacy default FC bins (FC1.25/1.50/1.75, from the old
    Power_125... names) by the agn_fc_<alpha> ones (FC0.25/0.50/0.75).
    Custom bins are kept. Returns True if the config was changed.
    """
    if config.get('BinFCVecLab') == _LEGACY_FC_BINS_LAB:
        config['BinFCVecLab'] = list(DEFAULT_FC_BINS_LAB)
        config['BinFCVec'] = {k: list(v) for k, v in DEFAULT_FC_BINS.items()}
        return True
    return False


def _component_values(components, kind):
    """Indices and values (alpha for kind='fc', T for kind='bb') of the AGN components."""
    get = agn_fc_exponent if kind == 'fc' else agn_bb_temperature
    idx, vals = [], []
    for i, comp in enumerate(components):
        v = get(comp)
        if v is not None:
            idx.append(i)
            vals.append(v)
    return np.array(idx, dtype=int), np.array(vals, dtype=float)


def pylight_properties(pars, ParList, pop, popComps, version, config, gal_dist=0.0):
    """
    Derive the pylight quantities (binned population vectors, mean ages and
    metallicities, masses, SFRs, fit quality) of a single STARLIGHT fit.

    Returns an ordered dict {name: float} in pylight.py column order.
    ``gal_dist`` (Mpc) is only needed for V4 files (masses / SFRs).
    """
    config = config or {}
    x_j, popMi, mcor_j, age_yr, Z_j = pop[:, 0], pop[:, 1], pop[:, 2], pop[:, 3], pop[:, 4]
    components = popComps

    popx = x_j * (100.0 / np.sum(x_j)) if np.sum(x_j) > 0 else x_j
    popm = mcor_j * (100.0 / np.sum(mcor_j)) if np.sum(mcor_j) > 0 else mcor_j
    popMi_norm = popMi * (100.0 / np.sum(popMi)) if np.sum(popMi) > 0 else popMi

    chi2 = _get_par(pars, ParList, 'chi2/Nl_eff')
    if np.isnan(chi2):
        chi2 = _get_par(pars, ParList, 'chi2]')
    adev = _get_par(pars, ParList, 'adev')
    snr = _get_par(pars, ParList, 'S/N in S/N window')
    av = _get_par(pars, ParList, 'AV_min')

    # --- Stellar masses ---
    NormFac = config.get('NormFac', 1.0)
    if version == 'V5':
        fobs_norm = _get_par(pars, ParList, 'fobs_norm')
        Mini_t = _get_par(pars, ParList, 'Mini_tot')
        Mcor_t = _get_par(pars, ParList, 'Mcor_tot')
    else:
        fobs_norm = _get_par(pars, ParList, 'fobs_norm (in input units)')
        Mini_tot_raw = _get_par(pars, ParList, 'Mini_tot')
        Mcor_tot_raw = _get_par(pars, ParList, 'Mcor_tot')
        if gal_dist and gal_dist > 0:
            gd = 3.08567758e24 * gal_dist  # Mpc -> cm
            Mini_t = NormFac * (Mini_tot_raw * 4.0 * np.pi) * gd**2 / 3.826e33
            Mcor_t = NormFac * (Mcor_tot_raw * 4.0 * np.pi) * gd**2 / 3.826e33
        else:
            Mini_t = Mcor_t = np.nan

    # --- Mean ages and metallicities (excluding AGN components: agn_fc_/agn_bb_..., always Z = 0) ---
    stellar = np.array([not is_agn_component(c) for c in components], dtype=bool) & (Z_j > 0)
    sumvec = [i for i in range(len(components)) if stellar[i]]
    sumvec = np.array(sumvec, dtype=int) if len(sumvec) > 0 else np.arange(len(popx))

    log_age = np.log10(np.where(age_yr > 0, age_yr, 1))
    px_s, pm_s = popx[sumvec], popm[sumvec]
    la_s, z_s = log_age[sumvec], Z_j[sumvec]
    sum_px_s, sum_pm_s = np.sum(px_s), np.sum(pm_s)
    # Light-weighted means are NOT renormalized to the stellar light: popx is the
    # fraction of the total light (FC included, sums to 100), so the FC light
    # stays in the budget and the stellar weights add up to < 100 %.
    meanAgex = np.sum((px_s / 100.0) * la_s) if np.sum(popx) > 0 else np.nan
    meanZx = np.sum((px_s / 100.0) * z_s) if np.sum(popx) > 0 else np.nan
    meanAgem = np.sum((pm_s / sum_pm_s) * la_s) if sum_pm_s > 0 else np.nan
    meanZm = np.sum((pm_s / sum_pm_s) * z_s) if sum_pm_s > 0 else np.nan

    out = {}

    # --- AGN FC and hot-dust bins ---
    if config.get('IsAGNComp', False):
        fcind, nu_vals = _component_values(components, 'fc')
        for fc_label in config.get('BinFCVecLab', []):
            bounds = config.get('BinFCVec', {}).get(fc_label, [0, 0])
            fc_mask = (nu_vals > bounds[0]) & (nu_vals <= bounds[1])
            out[fc_label] = float(np.sum(popx[fcind][fc_mask])) if len(fcind) else 0.0

        hdind, bb_vals = _component_values(components, 'bb')
        for hd_label in config.get('BinHDVecLab', []):
            bounds = config.get('BinHDVec', {}).get(hd_label, [0, 0])
            hd_mask = (bb_vals > bounds[0]) & (bb_vals <= bounds[1])
            out[hd_label] = float(np.sum(popx[hdind][hd_mask])) if len(hdind) else 0.0

    # --- Binned population vectors (light, then mass) ---
    bin_pop_vec = config.get('BinPopVec', {})
    pop_labels = config.get('BinPopVecLab', list(bin_pop_vec.keys()))
    for label in pop_labels:
        bounds = bin_pop_vec.get(label, [0, 0])
        mask = (age_yr > bounds[0]) & (age_yr <= bounds[1]) & stellar
        out[label] = float(np.sum(popx[mask]))
    for idx_m, label in enumerate(config.get('BinPopVecMassLab', [])):
        bounds = bin_pop_vec.get(pop_labels[idx_m], [0, 0]) if idx_m < len(pop_labels) else [0, 0]
        mask = (age_yr > bounds[0]) & (age_yr <= bounds[1]) & stellar
        out[label] = float(np.sum(popm[mask]))

    # --- Physical properties ---
    out['Av'] = av
    out['Mage_L'] = meanAgex
    out['Mage_M'] = meanAgem
    out['MZ_L'] = meanZx
    out['MZ_M'] = meanZm
    out['M*'] = Mcor_t
    out['M*in'] = Mini_t

    # --- SFR bins ---
    bin_sfr = config.get('BinSFR', {})
    for sfr_label in config.get('BinSFRLabs', list(bin_sfr.keys())):
        bounds = bin_sfr.get(sfr_label, [0, 0])
        mask = (age_yr > bounds[0]) & (age_yr <= bounds[1]) & stellar
        SF = bounds[1] - bounds[0]
        if SF > 0 and not np.isnan(Mini_t):
            out[sfr_label] = ((np.sum(popMi_norm[mask]) / 100.0) * Mini_t) / SF
        else:
            out[sfr_label] = np.nan

    # --- Fit quality ---
    out['F_Norm'] = fobs_norm
    out['Adev'] = adev
    out['ChiSqrt'] = chi2
    out['SNR'] = snr

    if config.get('SaveDist', True):
        out['GalDist'] = float(gal_dist)

    return out
