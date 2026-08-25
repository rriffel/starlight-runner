"""
masking.py — Spectral mask creation, presets, and I/O for STARLIGHT.
Manages masked wavelength intervals, emission line templates (Optical & NIR),
custom weights, and standard Starlight `.sm` mask files.
"""

import os
import numpy as np


OPTICAL_EMISSION_LINES = [
    {"name": "[O II] 3726, 3729", "low": 3710.0, "upp": 3744.0, "weight": 0.0},
    {"name": "[Ne III] 3869", "low": 3858.0, "upp": 3880.0, "weight": 0.0},
    {"name": "H8 + He I 3889", "low": 3880.0, "upp": 3905.0, "weight": 0.0},
    {"name": "Hepsilon 3970 + [Ne III]", "low": 3960.0, "upp": 3980.0, "weight": 0.0},
    {"name": "Hdelta 4102", "low": 4092.0, "upp": 4112.0, "weight": 0.0},
    {"name": "Hgamma 4340 + [O III] 4363", "low": 4330.0, "upp": 4375.0, "weight": 0.0},
    {"name": "He II 4686", "low": 4675.0, "upp": 4700.0, "weight": 0.0},
    {"name": "Hbeta 4861", "low": 4848.0, "upp": 4874.0, "weight": 0.0},
    {"name": "[O III] 4959, 5007", "low": 4940.0, "upp": 5028.0, "weight": 0.0},
    {"name": "[N I] 5198, 5200", "low": 5190.0, "upp": 5210.0, "weight": 0.0},
    {"name": "He I 5876 + Na I D", "low": 5866.0, "upp": 5916.0, "weight": 0.0},
    {"name": "[O I] 6300, 6364", "low": 6280.0, "upp": 6375.0, "weight": 0.0},
    {"name": "[N II] + Halpha + [N II] (6548, 6563, 6583)", "low": 6528.0, "upp": 6608.0, "weight": 0.0},
    {"name": "[S II] 6716, 6731", "low": 6696.0, "upp": 6752.0, "weight": 0.0},
    {"name": "[Ar III] 7136", "low": 7120.0, "upp": 7150.0, "weight": 0.0},
    {"name": "[O II] 7320, 7330", "low": 7310.0, "upp": 7340.0, "weight": 0.0},
    {"name": "[S III] 9069", "low": 9050.0, "upp": 9090.0, "weight": 0.0},
    {"name": "[S III] 9531", "low": 9510.0, "upp": 9555.0, "weight": 0.0},
]

NIR_EMISSION_AND_TELLURIC_LINES = [
    {"name": "He I 10830 + Pgamma", "low": 10800.0, "upp": 10970.0, "weight": 0.0},
    {"name": "Pbeta 12818", "low": 12790.0, "upp": 12850.0, "weight": 0.0},
    {"name": "[Fe II] 12567", "low": 12530.0, "upp": 12590.0, "weight": 0.0},
    {"name": "[Fe II] 16435", "low": 16400.0, "upp": 16470.0, "weight": 0.0},
    {"name": "Palpha 18751", "low": 18700.0, "upp": 18850.0, "weight": 0.0},
    {"name": "H2 1-0 S(1) 21218", "low": 21180.0, "upp": 21250.0, "weight": 0.0},
    {"name": "Brgamma 21661", "low": 21620.0, "upp": 21700.0, "weight": 0.0},
    {"name": "Telluric J-H gap", "low": 13400.0, "upp": 14200.0, "weight": 0.0},
    {"name": "Telluric H-K gap", "low": 18000.0, "upp": 19000.0, "weight": 0.0},
]


class SpectralMask:
    """
    Container for Starlight mask intervals.
    Each interval is (low_lambda, upp_lambda, weight, name).
    """

    def __init__(self, intervals=None):
        self.intervals = []
        if intervals:
            for item in intervals:
                self.add_interval(*item)

    def add_interval(self, low, upp, weight=0.0, name=""):
        low, upp = float(min(low, upp)), float(max(low, upp))
        self.intervals.append({
            "low": low,
            "upp": upp,
            "weight": float(weight),
            "name": str(name)
        })
        self.sort()

    def remove_interval(self, index):
        if 0 <= index < len(self.intervals):
            return self.intervals.pop(index)
        return None

    def clear(self):
        self.intervals.clear()

    def sort(self):
        self.intervals.sort(key=lambda x: x["low"])

    def to_array(self):
        """Returns numpy array of shape (N, 3): [low, upp, weight]."""
        if not self.intervals:
            return np.empty((0, 3))
        return np.array([[it["low"], it["upp"], it["weight"]] for it in self.intervals])

    def get_mask_vector(self, wl):
        """
        Evaluate mask on a 1D wavelength array.
        Returns weight_vector where default is 1.0 (unmasked), or weight for masked intervals.
        """
        wl = np.asarray(wl, dtype=np.float64)
        weights = np.ones_like(wl, dtype=np.float64)
        for it in self.intervals:
            in_range = (wl >= it["low"]) & (wl <= it["upp"])
            weights[in_range] = it["weight"]
        return weights

    def save_to_file(self, filepath):
        """
        Save mask to Starlight .mask format:
        First line: number of intervals (N)
        Subsequent lines: low_lambda upp_lambda weight
        """
        self.sort()
        os.makedirs(os.path.dirname(os.path.abspath(filepath)) or '.', exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(f"{len(self.intervals)}\n")
            for it in self.intervals:
                f.write(f"{it['low']:.2f} {it['upp']:.2f} {it['weight']:.2f}\n")
        return filepath

    @classmethod
    def load_from_file(cls, filepath):
        """
        Load mask from a Starlight .mask file.
        """
        mask = cls()
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Mask file not found: {filepath}")
            
        with open(filepath, 'r') as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith(('#', '!'))]
            
        if not lines:
            return mask
            
        # First line is usually the count N
        try:
            first_val = float(lines[0].split()[0])
            if len(lines[0].split()) == 1:
                data_lines = lines[1:]
            else:
                data_lines = lines
        except Exception:
            data_lines = lines

        for line in data_lines:
            parts = line.split()
            if len(parts) >= 2:
                low = float(parts[0])
                upp = float(parts[1])
                weight = float(parts[2]) if len(parts) >= 3 else 0.0
                name = " ".join(parts[3:]) if len(parts) >= 4 else ""
                mask.add_interval(low, upp, weight, name)
                
        return mask

    from_file = load_from_file

    @classmethod

    def from_preset(cls, preset_name="optical", wl_range=None):
        """
        Create a mask instance populated from standard presets.
        preset_name: 'optical', 'nir', or 'optical+nir'.
        """
        mask = cls()
        lines_to_add = []
        p_name = preset_name.lower()
        
        if "optical" in p_name:
            lines_to_add.extend(OPTICAL_EMISSION_LINES)
        if "nir" in p_name:
            lines_to_add.extend(NIR_EMISSION_AND_TELLURIC_LINES)

        for line in lines_to_add:
            if wl_range is not None:
                # Include only if overlaps with wl_range
                if line["upp"] < wl_range[0] or line["low"] > wl_range[1]:
                    continue
            mask.add_interval(line["low"], line["upp"], line["weight"], line["name"])
            
        return mask


def create_standard_mask(filepath, preset='optical', wl_range=None):
    """
    Utility function to generate and save a standard mask file directly.
    """
    mask = SpectralMask.from_preset(preset, wl_range=wl_range)
    mask.save_to_file(filepath)
    return mask
