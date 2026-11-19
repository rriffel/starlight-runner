"""
spectrum_io.py — Reading ASCII/CSV spectra and converting them to the plain
whitespace table the STARLIGHT Fortran binary expects
(``lambda flux [error [flag]]``, no header, no commas).

STARLIGHT reads the observed spectrum itself, so files such as

    wavelength,flux_mean
    3.700000e+03,7.001825e-19
    ...

cannot be passed to it directly. ``prepare_spectra_for_starlight`` writes a
STARLIGHT-ready copy of such files (``<name>.spec``) in a separate folder.
"""

import os
import shutil

import numpy as np
import pandas as pd

DEFAULT_CONVERTED_DIR = "starlight_input"

_COMMENT_CHARS = ('#', ';', '!')
_WL_NAMES = ("wavelength", "wave", "lambda", "lam", "wl", "loglam")
_FLUX_NAMES = ("flux", "flux_mean", "flam", "f", "spec", "data", "flux_obs")
_ERR_NAMES = ("err", "error", "eflux", "flux_err", "flux_error", "sigma", "flux_std",
              "std", "unc", "uncertainty", "noise", "ivar")
_FLAG_NAMES = ("flag", "flags", "mask")


def _first_data_line(path):
    with open(path, 'r', errors='replace') as fh:
        for line in fh:
            s = line.strip()
            if s and not s.startswith(_COMMENT_CHARS):
                return s
    return ""


def needs_conversion(path):
    """
    True if ``path`` is not a plain whitespace numeric table STARLIGHT can read
    (e.g. a CSV, or any file with a column-name header).
    """
    if os.path.splitext(path)[1].lower() in (".csv", ".fits", ".fit"):
        return True
    line = _first_data_line(path)
    if not line:
        return False
    try:
        [float(tok) for tok in line.split()]
        return False
    except ValueError:
        return True


def _pick(cols, names):
    low = [c.strip().lower() for c in cols]
    for n in names:
        if n in low:
            return low.index(n)
    return None


def read_spectrum_table(path):
    """
    Read an ASCII/CSV spectrum as a float array of shape (N, ncol) with the
    columns ordered lambda, flux[, error[, flag]].

    Comma-, semicolon-, tab- or whitespace-separated files are accepted, with
    or without a header line. With a header, columns are identified by name
    (``wavelength``/``lambda``, ``flux``/``flux_mean``, ``error``/``sigma``/
    ``ivar``, ``flag``); otherwise by position. Rows that are not numeric are
    dropped.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in (".fits", ".fit"):
        from .preprocessing import load_spectrum
        wl, flux, eflux = load_spectrum(path)
        cols = [wl, flux] + ([eflux] if eflux is not None else [])
        return np.column_stack(cols).astype(np.float64)

    first = _first_data_line(path)
    if ',' in first:
        sep = ','
    elif ';' in first:
        sep = ';'
    elif '\t' in first:
        sep = '\t'
    else:
        sep = r'\s+'

    tokens = [t for t in (first.split() if sep == r'\s+' else first.split(sep.strip() or None))]
    try:
        [float(t) for t in tokens]
        has_header = False
    except ValueError:
        has_header = True

    df = pd.read_csv(path, sep=sep, comment='#', header=0 if has_header else None,
                     engine='python', skipinitialspace=True)
    df = df.apply(pd.to_numeric, errors='coerce').dropna(how='all')
    if df.shape[1] < 2:
        raise ValueError(f"{path}: need at least two columns (lambda, flux); found {df.shape[1]}.")

    order = list(range(df.shape[1]))
    if has_header:
        cols = [str(c) for c in df.columns]
        i_wl = _pick(cols, _WL_NAMES)
        i_fx = _pick(cols, _FLUX_NAMES)
        i_er = _pick(cols, _ERR_NAMES)
        i_fl = _pick(cols, _FLAG_NAMES)
        if i_wl is None:
            i_wl = 0
        if i_fx is None:
            i_fx = next(i for i in range(df.shape[1]) if i not in (i_wl, i_er, i_fl))
        order = [i_wl, i_fx] + [i for i in (i_er, i_fl) if i is not None]
        if i_er is None and i_fl is None:
            rest = [i for i in range(df.shape[1]) if i not in (i_wl, i_fx)]
            order += rest[:2]

    data = df.iloc[:, order].to_numpy(dtype=np.float64)
    data = data[np.isfinite(data[:, 0])]

    if has_header and _pick([str(c) for c in df.columns], ("loglam",)) == order[0]:
        data[:, 0] = 10.0 ** data[:, 0]
    if has_header and len(order) > 2 and str(df.columns[order[2]]).strip().lower() == "ivar":
        iv = data[:, 2]
        data[:, 2] = np.where(iv > 0, 1.0 / np.sqrt(np.where(iv > 0, iv, 1.0)), 0.0)
    return data


def write_starlight_spectrum(data, path):
    """Write an (N, ncol) array as a STARLIGHT ASCII spectrum (no header)."""
    fmt = ['%.6f', '%.8e', '%.8e'][:min(3, data.shape[1])] + ['%d'] * max(0, data.shape[1] - 3)
    d = data.copy()
    if d.shape[1] > 3:
        d[:, 3:] = np.nan_to_num(d[:, 3:], nan=0).astype(int)
    np.savetxt(path, d, fmt=fmt)
    return path


def prepare_spectra_for_starlight(spec_files, converted_dir=DEFAULT_CONVERTED_DIR, require_error=False):
    """
    Make every spectrum in ``spec_files`` readable by STARLIGHT.

    If none needs conversion, returns ``(spec_files, None)`` unchanged.
    Otherwise all spectra are placed in ``converted_dir`` (STARLIGHT has a
    single obs_dir per grid): files needing conversion are written as
    ``<name>.spec``, the others are copied as they are. Returns
    ``(new_files, converted_dir)``.

    With ``require_error`` a converted spectrum without an error column raises
    ``ValueError`` (STARLIGHT would otherwise read garbage).
    """
    flags = [needs_conversion(f) for f in spec_files]
    if not any(flags):
        return list(spec_files), None

    os.makedirs(converted_dir, exist_ok=True)
    out = []
    seen = {}
    for f, conv in zip(spec_files, flags):
        if conv:
            data = read_spectrum_table(f)
            if require_error and data.shape[1] < 3:
                raise ValueError(
                    f"{os.path.basename(f)} has no error column, but 'Error spectrum available' "
                    "(IsErrSpecAvailable) is on. Turn it off or add an error column."
                )
            name = os.path.splitext(os.path.basename(f))[0] + ".spec"
            dest = os.path.join(converted_dir, name)
            write_starlight_spectrum(data, dest)
        else:
            name = os.path.basename(f)
            dest = os.path.join(converted_dir, name)
            if os.path.abspath(f) != os.path.abspath(dest):
                shutil.copyfile(f, dest)
        if name in seen:
            raise ValueError(f"Two input spectra map to the same STARLIGHT file '{name}': "
                             f"{seen[name]} and {f}")
        seen[name] = f
        out.append(dest)
    return out, converted_dir
