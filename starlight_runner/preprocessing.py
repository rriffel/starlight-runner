"""
preprocessing.py — Spectral preparation pipeline for STARLIGHT.
Handles file ingestion, NaN/inf cleaning, Galactic dereddening,
redshift transformation, regular rebinning, telluric cutouts, and .spec export.
"""

import os
import numpy as np
from scipy.interpolate import interp1d
import pandas as pd

from .reddening import deredden


DEFAULT_TELLURIC_REGIONS = [
    (0.0, 13400.0),
    (14200.0, 18000.0),
    (18700.0, 25000.0)
]


def load_spectrum(filepath):
    """
    Load spectrum from various formats: .txt, .dat, .csv, .spec, or .fits.
    Returns:
        wl (np.ndarray): Wavelength array
        flux (np.ndarray): Flux array
        eflux (np.ndarray or None): Error array if present, else None
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Spectrum file not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()

    if ext in [".fits", ".fit"]:
        try:
            from astropy.io import fits
            with fits.open(filepath) as hdul:
                header = hdul[0].header
                data = hdul[0].data
                if data is None and len(hdul) > 1:
                    data = hdul[1].data
                    header = hdul[1].header

                # Check if 1D array with WCS
                if isinstance(data, np.ndarray) and data.ndim == 1:
                    flux = data.astype(np.float64)
                    crval = header.get("CRVAL1", 1.0)
                    cdelt = header.get("CDELT1", header.get("CD1_1", 1.0))
                    crpix = header.get("CRPIX1", 1.0)
                    naxis1 = header.get("NAXIS1", len(flux))
                    wl = crval + (np.arange(naxis1) + 1.0 - crpix) * cdelt
                    eflux = None
                    return wl, flux, eflux
                # Check if table in HDU 1
                elif hasattr(data, "columns"):
                    colnames = [c.name.lower() for c in data.columns]
                    wl_col = next((c for c in data.columns.names if c.lower() in ["wave", "wavelength", "lambda", "loglam"]), None)
                    flx_col = next((c for c in data.columns.names if c.lower() in ["flux", "flam", "spec", "data"]), None)
                    err_col = next((c for c in data.columns.names if c.lower() in ["err", "error", "ivar", "eflux", "sigma"]), None)
                    
                    if wl_col and flx_col:
                        wl = np.asarray(data[wl_col], dtype=np.float64)
                        flux = np.asarray(data[flx_col], dtype=np.float64)
                        if "loglam" in wl_col.lower():
                            wl = 10.0 ** wl
                        if err_col:
                            eflux = np.asarray(data[err_col], dtype=np.float64)
                            if "ivar" in err_col.lower():
                                eflux = np.where(eflux > 0, 1.0 / np.sqrt(eflux), 1e-10)
                        else:
                            eflux = None
                        return wl, flux, eflux
        except Exception as e:
            pass  # Fallback to ascii reader

    # ASCII / CSV loading
    try:
        # Try pandas whitespace first
        df = pd.read_csv(filepath, comment='#', sep=r'\s+', header=None, engine='python')
        if df.shape[1] < 2:
            df = pd.read_csv(filepath, comment='#', sep=',', header=None)
        
        # Clean non-numeric rows if any header remained
        df = df.apply(pd.to_numeric, errors='coerce').dropna(how='all')
        
        wl = df.iloc[:, 0].to_numpy(dtype=np.float64)
        flux = df.iloc[:, 1].to_numpy(dtype=np.float64)
        
        if df.shape[1] >= 3:
            eflux = df.iloc[:, 2].to_numpy(dtype=np.float64)
        else:
            eflux = None
            
        return wl, flux, eflux
    except Exception as e:
        # Fallback to np.loadtxt
        data = np.loadtxt(filepath, comments=['#', ';', '!'])
        wl = data[:, 0]
        flux = data[:, 1]
        eflux = data[:, 2] if data.shape[1] >= 3 else None
        return wl, flux, eflux


def clean_spectrum(wl, flux, eflux=None, remove_nan=True, min_error=1e-20):
    """
    Remove NaNs, Infs, and handle error array validity.
    Also handles duplicate wavelength values by averaging flux and combining errors.
    """
    wl = np.asarray(wl, dtype=np.float64)
    flux = np.asarray(flux, dtype=np.float64)
    
    mask = np.isfinite(wl) & np.isfinite(flux)
    if eflux is not None:
        eflux = np.asarray(eflux, dtype=np.float64)
        mask = mask & np.isfinite(eflux)
        
    wl_clean = wl[mask]
    flux_clean = flux[mask]
    
    # Sort by wavelength if not already sorted
    sort_idx = np.argsort(wl_clean)
    wl_clean = wl_clean[sort_idx]
    flux_clean = flux_clean[sort_idx]
    
    if eflux is not None:
        eflux_clean = eflux[mask][sort_idx]
        # Replace negative or zero errors with reasonable floor or min_error
        invalid_err = (eflux_clean <= 0.0) | np.isnan(eflux_clean)
        if np.any(invalid_err):
            positive_errs = eflux_clean[~invalid_err]
            floor_val = np.median(positive_errs) if len(positive_errs) > 0 else min_error
            eflux_clean[invalid_err] = floor_val
            
        # Deduplicate identical wavelengths if present
        if len(wl_clean) != len(np.unique(wl_clean)):
            unique_wl, inv, counts = np.unique(wl_clean, return_inverse=True, return_counts=True)
            flux_clean = np.bincount(inv, weights=flux_clean) / counts
            eflux_sq = np.bincount(inv, weights=eflux_clean**2)
            eflux_clean = np.sqrt(eflux_sq) / counts
            wl_clean = unique_wl
            
        return wl_clean, flux_clean, eflux_clean

    # Deduplicate identical wavelengths if present (no eflux)
    if len(wl_clean) != len(np.unique(wl_clean)):
        unique_wl, inv, counts = np.unique(wl_clean, return_inverse=True, return_counts=True)
        flux_clean = np.bincount(inv, weights=flux_clean) / counts
        wl_clean = unique_wl
        
    return wl_clean, flux_clean, None


def cut_spectral_regions(wl, flux, eflux=None, regions=None):
    """
    Cut wavelength regions, keeping only pixels inside the specified intervals.
    `regions` is a list of tuples/lists: [(w_min1, w_max1), (w_min2, w_max2), ...]
    """
    if regions is None or len(regions) == 0:
        return wl, flux, eflux

    wl = np.asarray(wl, dtype=np.float64)
    flux = np.asarray(flux, dtype=np.float64)
    
    keep_mask = np.zeros(len(wl), dtype=bool)
    for (w_min, w_max) in regions:
        keep_mask |= ((wl >= w_min) & (wl <= w_max))
        
    wl_cut = wl[keep_mask]
    flux_cut = flux[keep_mask]
    
    if eflux is not None:
        eflux_cut = np.asarray(eflux, dtype=np.float64)[keep_mask]
        return wl_cut, flux_cut, eflux_cut
        
    return wl_cut, flux_cut, None


def exclude_spectral_regions(wl, flux, eflux=None, regions=None):
    """
    Exclude specified wavelength intervals (e.g. telluric absorption gaps).
    `regions` is a list of tuples/lists of regions to REMOVE: [(w_low1, w_upp1), ...]
    """
    if regions is None or len(regions) == 0:
        return wl, flux, eflux

    wl = np.asarray(wl, dtype=np.float64)
    flux = np.asarray(flux, dtype=np.float64)

    cut_mask = np.zeros(len(wl), dtype=bool)
    for (w_min, w_max) in regions:
        cut_mask |= ((wl >= min(w_min, w_max)) & (wl <= max(w_min, w_max)))

    keep_mask = ~cut_mask
    wl_cut = wl[keep_mask]
    flux_cut = flux[keep_mask]

    if eflux is not None:
        eflux_cut = np.asarray(eflux, dtype=np.float64)[keep_mask]
        return wl_cut, flux_cut, eflux_cut

    return wl_cut, flux_cut, None


def trim_spectral_bounds(wl, flux, eflux=None, wl_min=None, wl_max=None):
    """
    Trim spectrum to stay within [wl_min, wl_max] bounds.
    """
    wl = np.asarray(wl, dtype=np.float64)
    flux = np.asarray(flux, dtype=np.float64)

    mask = np.ones(len(wl), dtype=bool)
    if wl_min is not None:
        mask &= (wl >= wl_min)
    if wl_max is not None:
        mask &= (wl <= wl_max)

    wl_trim = wl[mask]
    flux_trim = flux[mask]

    if eflux is not None:
        eflux_trim = np.asarray(eflux, dtype=np.float64)[mask]
        return wl_trim, flux_trim, eflux_trim

    return wl_trim, flux_trim, None



def apply_redshift(wl, z):
    """
    Shift wavelength to rest-frame: lambda_rest = lambda_obs / (1 + z).
    """
    return np.asarray(wl, dtype=np.float64) / (1.0 + float(z))


def rebin_spectrum(wl, flux, eflux=None, step=1.0, wl_min=None, wl_max=None, kind='linear'):
    """
    Rebin flux and errors to a regular linear wavelength grid with step delta_lambda.
    Guarantees strictly non-repeating, regularly spaced wavelengths without floating-point drift.
    """
    wl = np.asarray(wl, dtype=np.float64)
    flux = np.asarray(flux, dtype=np.float64)
    
    # Ensure strictly increasing sorted array
    if not np.all(np.diff(wl) > 0):
        sort_idx = np.argsort(wl)
        wl = wl[sort_idx]
        flux = flux[sort_idx]
        if eflux is not None:
            eflux = np.asarray(eflux, dtype=np.float64)[sort_idx]
        
        # Deduplicate identical wavelengths
        if len(wl) != len(np.unique(wl)):
            unique_wl, inv, counts = np.unique(wl, return_inverse=True, return_counts=True)
            flux = np.bincount(inv, weights=flux) / counts
            if eflux is not None:
                eflux = np.sqrt(np.bincount(inv, weights=eflux**2)) / counts
            wl = unique_wl

    if wl_min is None:
        wl_min = np.ceil(wl[0])
    if wl_max is None:
        wl_max = np.floor(wl[-1])
        
    if wl_min >= wl_max:
        raise ValueError(f"Invalid rebinning range: [{wl_min}, {wl_max}]")
        
    # Exact regular grid using linspace
    num_points = int(np.floor((wl_max - wl_min) / step + 1e-6)) + 1
    wl_rebin = np.linspace(wl_min, wl_min + (num_points - 1) * step, num_points)
    
    f_interp = interp1d(wl, flux, kind=kind, fill_value="extrapolate", assume_sorted=True)
    flux_rebin = f_interp(wl_rebin)
    
    if eflux is not None:
        eflux = np.asarray(eflux, dtype=np.float64)
        ef_interp = interp1d(wl, eflux, kind=kind, fill_value="extrapolate", assume_sorted=True)
        eflux_rebin = np.maximum(ef_interp(wl_rebin), 1e-20)
        return wl_rebin, flux_rebin, eflux_rebin
        
    return wl_rebin, flux_rebin, None


def varsmooth(x, y, sig_x, xout=None, oversample=1):
    """
    Fourier convolution with a Gaussian with variable sigma per pixel
    using FFT and analytic Fourier Transform of the Gaussian (Cappellari 2022 / pPXF).
    
    :param x: coordinate array of every pixel (wavelength in Angstroms).
    :param y: input flux vector (or 2D array of column spectra).
    :param sig_x: Gaussian sigma of every pixel in units of x (Angstroms).
    :param oversample: oversampling factor before convolution (default 1).
    :param xout: optional output x coordinate.
    :return: convolved flux vector.
    """
    from scipy import interpolate
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    sig_x = np.asarray(sig_x, dtype=np.float64)
    
    sig_x = np.maximum(sig_x, 1e-6)
    
    dx = np.gradient(x)
    dx[dx == 0] = 1e-6
    sig = sig_x / dx
    sig_max = np.max(sig) * oversample
    xs = np.cumsum(sig_max / sig)
    n = int(np.ceil(xs[-1] - xs[0]))
    if n <= 1:
        return y.copy()
        
    x_new = np.linspace(xs[0], xs[-1], n)
    y_new = interpolate.interp1d(xs, y.T, bounds_error=False, fill_value="extrapolate")(x_new)

    npad = 2 ** int(np.ceil(np.log2(n)))
    ft = np.fft.rfft(y_new, npad)
    w = np.linspace(0, np.pi * sig_max, ft.shape[-1])
    ft_gau = np.exp(-0.5 * (w ** 2))
    y_conv = np.fft.irfft(ft * ft_gau, npad).T[:n]

    if xout is not None:
        xs = interpolate.interp1d(x, xs, bounds_error=False, fill_value="extrapolate")(xout)

    return interpolate.interp1d(x_new, y_conv.T, bounds_error=False, fill_value="extrapolate")(xs).T


def varsmooth_error(x, error, sig_x, xout=None, oversample=1):
    """
    Propagate uncertainties through variable-sigma convolution (Klein 2021 / PACCE).
    Convolves variance (error^2) with Gaussian kernel sig_x / sqrt(2).
    """
    from scipy import interpolate
    x = np.asarray(x, dtype=np.float64)
    error = np.asarray(error, dtype=np.float64)
    sig_x = np.asarray(sig_x, dtype=np.float64)

    y = error ** 2
    sig_x = sig_x / np.sqrt(2.0)
    sig_x = np.maximum(sig_x, 1e-6)

    dx = np.gradient(x)
    dx[dx == 0] = 1e-6
    sig = sig_x / dx
    sig_max = np.max(sig) * oversample
    xs = np.cumsum(sig_max / sig)
    n = int(np.ceil(xs[-1] - xs[0]))
    if n <= 1:
        return error.copy()
        
    x_new = np.linspace(xs[0], xs[-1], n)
    y_new = interpolate.interp1d(xs, y.T, bounds_error=False, fill_value="extrapolate")(x_new)

    npad = 2 ** int(np.ceil(np.log2(n)))
    ft = np.fft.rfft(y_new, npad)
    w = np.linspace(0, np.pi * sig_max, ft.shape[-1])
    ft_gau = np.exp(-0.5 * (w ** 2))
    y_conv = np.fft.irfft(ft * ft_gau, npad).T[:n]

    if xout is not None:
        xs = interpolate.interp1d(x, xs, bounds_error=False, fill_value="extrapolate")(xout)

    conv_var = interpolate.interp1d(x_new, y_conv.T, bounds_error=False, fill_value="extrapolate")(xs).T
    return np.sqrt(np.maximum(conv_var, 0.0))


def downgrade_resolution(
    wl, flux, eflux=None,
    mode="R",
    val_ini=None,
    val_target=None,
    file_ini=None,
    file_target=None,
    oversample=1
):
    """
    Downgrades spectral resolution using PACCE / pPXF variable-sigma Gaussian convolution (varsmooth).
    
    Parameters:
        wl (np.ndarray): Wavelength array (Angstroms).
        flux (np.ndarray): Flux array.
        eflux (np.ndarray, optional): Flux uncertainty array.
        mode (str): 'R' (Resolving power lambda/delta_lambda), 
                    'sigma' (Velocity dispersion in km/s),
                    'FWHM' (FWHM in Angstroms).
        val_ini (float, optional): Initial scalar resolution value.
        val_target (float, optional): Target scalar resolution value.
        file_ini (str, optional): Path to 2-column text file (wavelength, val) for initial resolution.
        file_target (str, optional): Path to 2-column text file for target resolution.
        oversample (int): Oversampling factor for FFT convolution.
        
    Returns:
        wl, flux_downgraded, eflux_downgraded
    """
    from scipy import interpolate
    wl = np.asarray(wl, dtype=np.float64)
    flux = np.asarray(flux, dtype=np.float64)
    c_kms = 299792.458
    fwhm_factor = 2.3548200450309493  # 2 * sqrt(2 * ln(2))

    # 1. Evaluate Initial Resolution Array
    if file_ini and os.path.exists(file_ini):
        data_ini = np.loadtxt(file_ini)
        f_interp = interpolate.interp1d(data_ini[:, 0], data_ini[:, 1], bounds_error=False, fill_value="extrapolate")
        raw_ini = f_interp(wl)
    elif val_ini is not None and float(val_ini) > 0:
        raw_ini = np.full_like(wl, float(val_ini))
    else:
        return wl, flux.copy(), (eflux.copy() if eflux is not None else None)

    # 2. Evaluate Target Resolution Array
    if file_target and os.path.exists(file_target):
        data_tgt = np.loadtxt(file_target)
        f_interp = interpolate.interp1d(data_tgt[:, 0], data_tgt[:, 1], bounds_error=False, fill_value="extrapolate")
        raw_tgt = f_interp(wl)
    elif val_target is not None and float(val_target) > 0:
        raw_tgt = np.full_like(wl, float(val_target))
    else:
        return wl, flux.copy(), (eflux.copy() if eflux is not None else None)

    # 3. Convert both to FWHM(lambda) in Angstroms
    mode_str = mode.lower()
    if "r" in mode_str:
        # Resolving power R = lambda / FWHM -> FWHM = lambda / R
        fwhm_ini = np.divide(wl, np.maximum(raw_ini, 1.0))
        fwhm_tgt = np.divide(wl, np.maximum(raw_tgt, 1.0))
    elif "sigma" in mode_str:
        # Velocity dispersion sigma in km/s -> FWHM = (sigma * 2.355 / c) * lambda
        fwhm_ini = (raw_ini * fwhm_factor / c_kms) * wl
        fwhm_tgt = (raw_tgt * fwhm_factor / c_kms) * wl
    else:  # FWHM in Angstroms
        fwhm_ini = raw_ini
        fwhm_tgt = raw_tgt

    # 4. Calculate Differential Convolution Sigma (in Angstroms)
    diff_fwhm_sq = np.maximum(0.0, fwhm_tgt**2 - fwhm_ini**2)
    sig_conv = np.sqrt(diff_fwhm_sq) / fwhm_factor

    if np.all(sig_conv <= 1e-4):
        # Target resolution is higher than or equal to initial, no smoothing needed
        return wl, flux.copy(), (eflux.copy() if eflux is not None else None)

    sig_conv = np.clip(sig_conv, 0.001, None)

    # 5. Convolve flux and errors
    flux_smooth = varsmooth(wl, flux, sig_x=sig_conv, oversample=oversample)
    
    if eflux is not None:
        eflux_arr = np.asarray(eflux, dtype=np.float64)
        eflux_smooth = varsmooth_error(wl, eflux_arr, sig_x=sig_conv, oversample=oversample)
        return wl, flux_smooth, eflux_smooth

    return wl, flux_smooth, None


def save_spec_file(filepath, wl, flux, eflux=None, flags=None):
    """
    Save spectrum to Starlight ASCII .spec format:
    col 1: Wavelength (Angstroms)
    col 2: Flux
    col 3: Error (optional, default 1e-20 if none)
    col 4: Flag (optional, default 0)
    """
    wl = np.asarray(wl, dtype=np.float64)
    flux = np.asarray(flux, dtype=np.float64)
    
    if eflux is None:
        # Default nominal error of 5% of flux or small positive constant
        eflux = np.maximum(np.abs(flux) * 0.05, 1e-20)
    else:
        eflux = np.asarray(eflux, dtype=np.float64)

    if flags is None:
        data = np.column_stack((wl, flux, eflux))
        fmt = ['%.4f', '%.7e', '%.7e']
    else:
        flags = np.asarray(flags, dtype=int)
        data = np.column_stack((wl, flux, eflux, flags))
        fmt = ['%.4f', '%.7e', '%.7e', '%d']
        
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    np.savetxt(filepath, data, fmt=fmt, delimiter=' ')
    return filepath


def preprocess_pipeline(
    filepath,
    z=0.0,
    av=0.0,
    ebv=None,
    rv=3.1,
    reddening_law="ccm",
    downgrade_res_enabled=False,
    res_mode="R",
    res_val_ini=None,
    res_val_target=None,
    res_file_ini=None,
    res_file_target=None,
    rebin_step=1.0,
    telluric_regions=None,
    output_spec_path=None
):
    """
    Complete high-level processing pipeline:
    1. Load spectrum & clean NaNs/Infs
    2. Physical corrections: Deredden (Galactic extinction) & Redshift correction (rest-frame)
    3. Downgrade resolution (Optional: varsmooth Fourier convolution)
    4. Rebin to regular grid
    5. Cut telluric windows (if specified)
    6. Save to .spec (if path specified)
    """
    raw_wl, raw_flx, raw_eflx = load_spectrum(filepath)
    wl_c, flx_c, eflx_c = clean_spectrum(raw_wl, raw_flx, raw_eflx)
    
    # 2. Physical Corrections: Dereddening
    wl_deredd, flx_deredd, eflx_deredd = deredden(
        wl_c, flx_c, eflux=eflx_c, law=reddening_law, av=av, ebv=ebv, rv=rv
    )
    
    # Redshift (rest-frame shift)
    wl_rest = apply_redshift(wl_deredd, z)
    flx_curr = flx_deredd
    eflx_curr = eflx_deredd

    # 3. Downgrade Resolution (Optional)
    if downgrade_res_enabled:
        wl_rest, flx_curr, eflx_curr = downgrade_resolution(
            wl_rest, flx_curr, eflux=eflx_curr,
            mode=res_mode, val_ini=res_val_ini, val_target=res_val_target,
            file_ini=res_file_ini, file_target=res_file_target
        )
    
    # 4. Rebin
    wl_rebin, flx_rebin, eflx_rebin = rebin_spectrum(
        wl_rest, flx_curr, eflux=eflx_curr, step=rebin_step
    )
    
    # 5. Telluric cut
    if telluric_regions is not None and len(telluric_regions) > 0:
        wl_final, flx_final, eflx_final = cut_spectral_regions(
            wl_rebin, flx_rebin, eflux=eflx_rebin, regions=telluric_regions
        )
    else:
        wl_final, flx_final, eflx_final = wl_rebin, flx_rebin, eflx_rebin
        
    if output_spec_path:
        save_spec_file(output_spec_path, wl_final, flx_final, eflx_final)
        
    return wl_final, flx_final, eflx_final

