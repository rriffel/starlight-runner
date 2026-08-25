"""
reddening.py — Comprehensive collection of interstellar extinction and attenuation laws.
Includes Cardelli et al. (1989), Calzetti et al. (2000), Fitzpatrick (1999), Seaton (1979),
Gordon et al. (2024 SMC), and dereddening / reddening utilities.
"""

import numpy as np


def ccm_89_law(wavelength_angstroms, rv=3.1):
    """
    Cardelli, Clayton, & Mathis (1989, ApJ, 345, 245) extinction law.
    Returns A(lambda) / A_V.
    """
    wl = np.atleast_1d(np.asarray(wavelength_angstroms, dtype=np.float64))
    x = 10000.0 / np.maximum(wl, 1e-5)  # inverse microns
    
    # Optical / NIR (0.3 <= x < 1.1)
    a_ir = 0.574 * (x**1.61)
    b_ir = -0.527 * (x**1.61)
    q_ir = a_ir + b_ir / rv

    # Optical / NIR (1.1 <= x < 3.3)
    y_opt = x - 1.82
    a_opt = (1.0 + 0.17699*y_opt - 0.50447*(y_opt**2) - 0.02427*(y_opt**3)
             + 0.72085*(y_opt**4) + 0.01979*(y_opt**5) - 0.77530*(y_opt**6)
             + 0.32999*(y_opt**7))
    b_opt = (1.41338*y_opt + 2.28305*(y_opt**2) + 1.07233*(y_opt**3)
             - 5.38434*(y_opt**4) - 0.62251*(y_opt**5) + 5.30260*(y_opt**6)
             - 2.09002*(y_opt**7))
    q_opt = a_opt + b_opt / rv

    # UV (3.3 <= x < 8.0)
    y_bump = x - 5.9
    fa = np.where(x >= 5.9, -0.04473*(y_bump**2) - 0.009779*(y_bump**3), 0.0)
    fb = np.where(x >= 5.9, 0.2130*(y_bump**2) + 0.1207*(y_bump**3), 0.0)
    a_uv = 1.752 - 0.316*x - 0.104/((x - 4.67)**2 + 0.341) + fa
    b_uv = -3.090 + 1.825*x + 1.206/((x - 4.62)**2 + 0.263) + fb
    q_uv = a_uv + b_uv / rv

    # Far-UV (8.0 <= x <= 10.0)
    y_fuv = x - 8.0
    a_fuv = -1.073 - 0.628*y_fuv + 0.137*(y_fuv**2) - 0.070*(y_fuv**3)
    b_fuv = 13.670 + 4.257*y_fuv - 0.420*(y_fuv**2) + 0.374*(y_fuv**3)
    q_fuv = a_fuv + b_fuv / rv

    q = np.where(
        (x >= 8.0) & (x <= 10.0), q_fuv,
        np.where((x >= 3.3) & (x < 8.0), q_uv,
        np.where((x >= 1.1) & (x < 3.3), q_opt,
        np.where((x >= 0.3) & (x < 1.1), q_ir,
        np.where(x < 0.3, 0.574 * (np.maximum(x, 0.01)**1.61), 1.0))))
    )
    return np.maximum(q, 0.0)


def calzetti_00_law(wavelength_angstroms, rv=4.05):
    """
    Calzetti et al. (2000, ApJ, 533, 682) starburst attenuation law.
    Returns A(lambda) / A_V where A_V = E(B-V) * R_V.
    """
    wl = np.atleast_1d(np.asarray(wavelength_angstroms, dtype=np.float64))
    x = 10000.0 / np.maximum(wl, 1e-5)
    
    # k(lambda) for 0.12 um <= lambda <= 0.63 um
    k1 = 2.659 * (-2.156 + 1.509*x - 0.198*(x**2) + 0.011*(x**3)) + rv
    # k(lambda) for 0.63 um < lambda <= 2.2 um
    k2 = 2.659 * (-1.857 + 1.040*x) + rv
    # Extrapolation for NIR > 2.2 um
    k_nir = 2.659 * (-1.857 + 1.040*(10000.0 / 22000.0)) * (wl / 22000.0)**(-1.5) + rv
    
    k = np.where(
        (wl >= 1200.0) & (wl <= 6300.0), k1,
        np.where((wl > 6300.0) & (wl <= 22000.0), k2,
        np.where(wl > 22000.0, k_nir, k1))
    )
    return np.maximum(k / rv, 0.0)


def fitzpatrick_99_law(wavelength_angstroms, rv=3.1):
    """
    Fitzpatrick (1999, PASP, 111, 63) extinction law.
    Returns A(lambda) / A_V.
    """
    wl = np.atleast_1d(np.asarray(wavelength_angstroms, dtype=np.float64))
    x = 10000.0 / np.maximum(wl, 1e-5)
    
    c1 = -0.17 + 0.39 * rv
    c2 = 0.70 + 0.40 * c1
    c3 = 3.23
    c4 = 0.41
    x0 = 4.596
    gamma = 0.99
    
    # UV term
    d = x**2 / ((x**2 - x0**2)**2 + (x * gamma)**2)
    f_uv = c1 + c2 * x + c3 * d
    f_fuv = np.where(x > 5.9, c4 * (0.5392 * (x - 5.9)**2 + 0.05644 * (x - 5.9)**3), 0.0)
    ebv_uv = f_uv + f_fuv
    
    # Optical spline approximation
    # k(V) = 0, k(B) = 1
    ebv_opt = (0.000 + 0.370 * (x - 1.82) + 0.420 * (x - 1.82)**2 
               - 0.180 * (x - 1.82)**3) * (x >= 1.0) * (x < 3.3)
    
    # IR power law
    ebv_ir = (-rv + rv * (x / 1.82)**1.8) * (x < 1.0)
    
    ebv_all = np.where(x >= 3.3, ebv_uv, np.where(x >= 1.0, ebv_opt, ebv_ir))
    al_av = 1.0 + ebv_all / rv
    return np.maximum(al_av, 0.0)


def seaton_79_law(wavelength_angstroms, rv=3.1):
    """
    Seaton (1979, MNRAS, 187, 73P) extinction law.
    Returns A(lambda) / A_V.
    """
    wl = np.atleast_1d(np.asarray(wavelength_angstroms, dtype=np.float64))
    x = 10000.0 / np.maximum(wl, 1e-5)
    
    # Optical: 1.0 <= x <= 2.75
    opt = 1.0 + (x - 1.83) * 0.8
    # UV: 2.75 < x <= 3.65
    uv1 = 1.56 + 1.048 * (x - 2.75)
    # UV bump: 3.65 < x <= 7.14
    uv2 = 2.29 + 0.848 * (x - 3.65) + 1.01 / ((x - 4.60)**2 + 0.280)
    # Far UV: 7.14 < x <= 10.0
    uv3 = 16.17 - 3.29 * x + 0.204 * x**2
    
    ebv = np.where(
        x < 1.0, opt,
        np.where(x <= 2.75, opt,
        np.where(x <= 3.65, uv1,
        np.where(x <= 7.14, uv2, uv3)))
    )
    return np.maximum(ebv / rv, 0.0)


def gordon_24_smc_law(wavelength_angstroms, rv=2.74):
    """
    Gordon et al. (2024) Small Magellanic Cloud (SMC) bar extinction law.
    Returns A(lambda) / A_V.
    """
    wl = np.atleast_1d(np.asarray(wavelength_angstroms, dtype=np.float64))
    x = 10000.0 / np.maximum(wl, 1e-5)
    
    # Linear rising UV without bump + power-law IR
    c1, c2, c3, c4 = -4.959, 2.264, 0.389, 0.461
    x0, gamma = 4.60, 1.0
    
    d = x**2 / ((x**2 - x0**2)**2 + (x * gamma)**2)
    f_uv = c1 + c2 * x + c3 * d
    f_fuv = np.where(x > 5.9, c4 * (0.5392 * (x - 5.9)**2 + 0.05644 * (x - 5.9)**3), 0.0)
    ebv = np.where(x >= 3.0, f_uv + f_fuv, (x / 1.82)**1.6 - 1.0)
    al_av = 1.0 + ebv / rv
    return np.maximum(al_av, 0.0)


REDDENING_LAWS = {
    "CCM (Cardelli+89 MW)": ccm_89_law,
    "Calzetti (2000 Starburst)": calzetti_00_law,
    "Fitzpatrick (1999 MW)": fitzpatrick_99_law,
    "Seaton (1979)": seaton_79_law,
    "Gordon+24 (SMC Bar)": gordon_24_smc_law,
}

LAW_ALIASES = {
    "ccm": ccm_89_law,
    "ccm89": ccm_89_law,
    "cardelli": ccm_89_law,
    "cal": calzetti_00_law,
    "cal00": calzetti_00_law,
    "calzetti": calzetti_00_law,
    "fitzpatrick": fitzpatrick_99_law,
    "ftzpt": fitzpatrick_99_law,
    "f99": fitzpatrick_99_law,
    "seaton": seaton_79_law,
    "smc": gordon_24_smc_law,
    "gordon": gordon_24_smc_law,
}


def get_al_av(wavelength_angstroms, law="ccm", rv=3.1):
    """
    Get A(lambda) / A_V for given wavelength and law name.
    """
    law_key = str(law).strip().lower()
    if law_key in LAW_ALIASES:
        func = LAW_ALIASES[law_key]
    else:
        # Match from dictionary keys
        func = ccm_89_law
        for k, v in REDDENING_LAWS.items():
            if law_key in k.lower():
                func = v
                break
    return func(wavelength_angstroms, rv=rv)


def deredden(wavelength, flux, eflux=None, law="ccm", av=None, ebv=None, rv=3.1):
    """
    Correct a spectrum for interstellar reddening (dereddening).
    
    F_corr = F_obs * 10^(0.4 * A_lambda)
    
    Parameters:
        wavelength : array-like (Angstroms)
        flux : array-like
        eflux : array-like, optional
        law : str ('ccm', 'calzetti', 'fitzpatrick', 'seaton', 'smc')
        av : float, visual extinction in magnitudes (A_V)
        ebv : float, E(B-V) in magnitudes (if av is not given, av = ebv * rv)
        rv : float, total-to-selective extinction ratio R_V (default 3.1)
        
    Returns:
        wl, flux_corr, eflux_corr (or wl, flux_corr if eflux is None)
    """
    wl = np.asarray(wavelength, dtype=np.float64)
    flx = np.asarray(flux, dtype=np.float64)
    
    if av is None:
        if ebv is not None:
            av = float(ebv) * float(rv)
        else:
            av = 0.0
            
    if av == 0.0:
        if eflux is not None:
            return wl, flx.copy(), np.asarray(eflux, dtype=np.float64).copy()
        return wl, flx.copy()
        
    al_av = get_al_av(wl, law=law, rv=rv)
    a_lambda = av * al_av
    correction_factor = 10.0 ** (0.4 * a_lambda)
    
    flx_corr = flx * correction_factor
    
    if eflux is not None:
        eflx = np.asarray(eflux, dtype=np.float64)
        eflx_corr = eflx * correction_factor
        return wl, flx_corr, eflx_corr
        
    return wl, flx_corr


def redden(wavelength, flux, eflux=None, law="ccm", av=None, ebv=None, rv=3.1):
    """
    Apply interstellar extinction (reddening) to a spectrum.
    
    F_red = F_unred * 10^(-0.4 * A_lambda)
    """
    wl = np.asarray(wavelength, dtype=np.float64)
    flx = np.asarray(flux, dtype=np.float64)
    
    if av is None:
        if ebv is not None:
            av = float(ebv) * float(rv)
        else:
            av = 0.0
            
    if av == 0.0:
        if eflux is not None:
            return wl, flx.copy(), np.asarray(eflux, dtype=np.float64).copy()
        return wl, flx.copy()
        
    al_av = get_al_av(wl, law=law, rv=rv)
    a_lambda = av * al_av
    attenuation_factor = 10.0 ** (-0.4 * a_lambda)
    
    flx_red = flx * attenuation_factor
    
    if eflux is not None:
        eflx = np.asarray(eflux, dtype=np.float64)
        eflx_red = eflx * attenuation_factor
        return wl, flx_red, eflx_red
        
    return wl, flx_red
