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
                comp = tokens[8] if len(tokens) > 8 else (tokens[7] if len(tokens) > 7 else f"ssp_{int(j)}")
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


def _component_values(components, tag):
    """Indices and numeric values (alpha or T) of AGN components whose label contains ``tag``."""
    import re
    idx, vals = [], []
    for i, comp in enumerate(components):
        comp_str = str(comp)
        if tag not in comp_str:
            continue
        ptmp = re.split(r'_', comp_str)
        try:
            v = float(ptmp[1])
        except (IndexError, ValueError):
            match = re.search(r'[\d\.]+', comp_str)
            v = float(match.group()) if match else 0
        if tag == 'Power':
            v /= 100.0
        idx.append(i)
        vals.append(v)
    return np.array(idx, dtype=int), np.array(vals)


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

    # --- Mean ages and metallicities (excluding AGN components) ---
    sumvec = [i for i, comp in enumerate(components)
              if 'BB_' not in str(comp) and 'Power' not in str(comp)]
    sumvec = np.array(sumvec, dtype=int) if len(sumvec) > 0 else np.arange(len(popx))

    log_age = np.log10(np.where(age_yr > 0, age_yr, 1))
    px_s, pm_s = popx[sumvec], popm[sumvec]
    la_s, z_s = log_age[sumvec], Z_j[sumvec]
    sum_px_s, sum_pm_s = np.sum(px_s), np.sum(pm_s)
    meanAgex = np.sum((px_s / sum_px_s) * la_s) if sum_px_s > 0 else np.nan
    meanZx = np.sum((px_s / sum_px_s) * z_s) if sum_px_s > 0 else np.nan
    meanAgem = np.sum((pm_s / sum_pm_s) * la_s) if sum_pm_s > 0 else np.nan
    meanZm = np.sum((pm_s / sum_pm_s) * z_s) if sum_pm_s > 0 else np.nan

    out = {}

    # --- AGN FC and hot-dust bins ---
    if config.get('IsAGNComp', False):
        fcind, nu_vals = _component_values(components, 'Power')
        for fc_label in config.get('BinFCVecLab', []):
            bounds = config.get('BinFCVec', {}).get(fc_label, [0, 0])
            fc_mask = (nu_vals > bounds[0]) & (nu_vals <= bounds[1])
            out[fc_label] = float(np.sum(popx[fcind][fc_mask])) if len(fcind) else 0.0

        hdind, bb_vals = _component_values(components, 'BB_')
        for hd_label in config.get('BinHDVecLab', []):
            bounds = config.get('BinHDVec', {}).get(hd_label, [0, 0])
            hd_mask = (bb_vals > bounds[0]) & (bb_vals <= bounds[1])
            out[hd_label] = float(np.sum(popx[hdind][hd_mask])) if len(hdind) else 0.0

    # --- Binned population vectors (light, then mass) ---
    bin_pop_vec = config.get('BinPopVec', {})
    pop_labels = config.get('BinPopVecLab', list(bin_pop_vec.keys()))
    for label in pop_labels:
        bounds = bin_pop_vec.get(label, [0, 0])
        mask = (age_yr > bounds[0]) & (age_yr <= bounds[1])
        out[label] = float(np.sum(popx[mask]))
    for idx_m, label in enumerate(config.get('BinPopVecMassLab', [])):
        bounds = bin_pop_vec.get(pop_labels[idx_m], [0, 0]) if idx_m < len(pop_labels) else [0, 0]
        mask = (age_yr > bounds[0]) & (age_yr <= bounds[1])
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
        mask = (age_yr > bounds[0]) & (age_yr <= bounds[1])
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
