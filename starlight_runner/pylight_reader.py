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
