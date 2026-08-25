"""
parser.py — Modern parser for STARLIGHT output files (.out).
Extracts synthesis parameters, population vectors (light/mass fractions, age, metallicity),
synthetic spectrum tables, residuals, and mean physical stellar population properties.
"""

import os
import re
import numpy as np
import pandas as pd


class StarlightOutput:
    """
    Data structure representing the parsed results of a single STARLIGHT .out file.
    """

    def __init__(self, filepath=None):
        self.filepath = filepath
        self.version = "V4"
        self.filename = os.path.basename(filepath) if filepath else ""
        
        # Fit quality & global parameters
        self.chi2 = np.nan
        self.chi2_eff = np.nan
        self.adev = np.nan
        self.fobs_norm = np.nan
        self.snr = np.nan
        self.av = np.nan
        self.yav = np.nan
        self.v0 = np.nan
        self.vd = np.nan
        self.mini_tot = np.nan
        self.mcor_tot = np.nan
        self.sum_x = np.nan
        self.n_base = 0

        # Data arrays & DataFrames
        self.pop_vector = pd.DataFrame()
        self.spectrum = pd.DataFrame()

        # Mean population properties
        self.mean_log_age_l = np.nan
        self.mean_log_age_m = np.nan
        self.mean_z_l = np.nan
        self.mean_z_m = np.nan

        # Age Bins (Young < 100 Myr, Intermediate 100 Myr - 2 Gyr, Old > 2 Gyr)
        self.x_young = 0.0
        self.x_intermediate = 0.0
        self.x_old = 0.0
        self.m_young = 0.0
        self.m_intermediate = 0.0
        self.m_old = 0.0

        if filepath:
            self.parse(filepath)

    def parse(self, filepath):
        """Parse a STARLIGHT .out file."""
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"STARLIGHT output file not found: {filepath}")

        with open(filepath, 'r') as f:
            lines = f.readlines()

        if len(lines) < 20:
            raise ValueError(f"File too short to be a valid STARLIGHT output: {filepath}")

        # Check version
        if any("PANcMExStarlight" in l for l in lines[:5]):
            self.version = "V5"
        else:
            self.version = "V4"

        # 1. Parse header scalar parameters
        for line in lines:
            if "[chi2/Nl_eff]" in line or "[chi2/Nl_eff" in line:
                try: self.chi2_eff = float(line.split()[0])
                except: pass
            elif "chi2]" in line and "[chi2/Nl_eff" not in line:
                try: self.chi2 = float(line.split()[1])
                except: pass
            elif "[adev (%)]" in line:
                try: self.adev = float(line.split()[0])
                except: pass
            elif "[fobs_norm" in line:
                try: self.fobs_norm = float(line.split()[0])
                except: pass
            elif "[S/N in S/N window]" in line:
                try: self.snr = float(line.split()[0])
                except: pass
            elif "[AV_min  (mag)]" in line or "[AV_min" in line:
                try: self.av = float(line.split()[0])
                except: pass
            elif "[YAV_min" in line:
                try: self.yav = float(line.split()[0])
                except: pass
            elif "[v0_min  (km/s)]" in line or "[v0_min" in line:
                try: self.v0 = float(line.split()[0])
                except: pass
            elif "[vd_min  (km/s)]" in line or "[vd_min" in line:
                try: self.vd = float(line.split()[0])
                except: pass
            elif "[Mini_tot" in line:
                try: self.mini_tot = float(line.split()[0])
                except: pass
            elif "[Mcor_tot" in line:
                try: self.mcor_tot = float(line.split()[0])
                except: pass
            elif "[sum-of-x (%)]" in line:
                try: self.sum_x = float(line.split()[0])
                except: pass
            elif "[N_base]" in line:
                try: self.n_base = int(line.split()[0])
                except: pass

        if np.isnan(self.chi2) and not np.isnan(self.chi2_eff):
            self.chi2 = self.chi2_eff

        # 2. Locate Population Vector Table and Spectrum Table
        pop_start = None
        pop_end = None
        spec_start = None

        for idx, line in enumerate(lines):
            if "x_j(%)" in line and pop_start is None:
                pop_start = idx + 1
            elif ("## Synthesis Results" in line or "## Synthetic spectrum" in line) and pop_start is not None and pop_end is None:
                pop_end = idx
            elif "## Synthetic spectrum" in line:
                # header format: ## Synthetic spectrum (Best Model) ##l_obs f_obs f_syn wei
                spec_start = idx + 1

        # 3. Parse Population Vectors
        pop_rows = []
        if pop_start is not None and pop_end is not None:
            for line in lines[pop_start:pop_end]:
                tokens = line.strip().split()
                if len(tokens) >= 7:
                    try:
                        j = int(tokens[0])
                        x_j = float(tokens[1])
                        mini_j = float(tokens[2])
                        mcor_j = float(tokens[3])
                        age_j = float(tokens[4])
                        z_j = float(tokens[5])
                        lm_j = float(tokens[6])
                        base_spec = tokens[7] if len(tokens) > 7 else f"ssp_{j}"
                        label = tokens[8] if len(tokens) > 8 else base_spec
                        pop_rows.append({
                            "j": j,
                            "x_j": x_j,
                            "mini_j": mini_j,
                            "mcor_j": mcor_j,
                            "age_yr": age_j,
                            "log_age": np.log10(max(age_j, 1.0)),
                            "Z": z_j,
                            "LM_j": lm_j,
                            "base_file": base_spec,
                            "label": label
                        })
                    except (ValueError, IndexError):
                        continue

        self.pop_vector = pd.DataFrame(pop_rows)

        # 4. Compute Weighted Means and Age Bins
        if not self.pop_vector.empty:
            total_x = self.pop_vector["x_j"].sum()
            total_m = self.pop_vector["mcor_j"].sum()

            if total_x > 0:
                self.mean_log_age_l = np.sum(self.pop_vector["x_j"] * self.pop_vector["log_age"]) / total_x
                self.mean_z_l = np.sum(self.pop_vector["x_j"] * self.pop_vector["Z"]) / total_x

                y_mask = self.pop_vector["age_yr"] <= 1.0e8
                i_mask = (self.pop_vector["age_yr"] > 1.0e8) & (self.pop_vector["age_yr"] <= 2.0e9)
                o_mask = self.pop_vector["age_yr"] > 2.0e9

                self.x_young = self.pop_vector.loc[y_mask, "x_j"].sum()
                self.x_intermediate = self.pop_vector.loc[i_mask, "x_j"].sum()
                self.x_old = self.pop_vector.loc[o_mask, "x_j"].sum()

            if total_m > 0:
                self.mean_log_age_m = np.sum(self.pop_vector["mcor_j"] * self.pop_vector["log_age"]) / total_m
                self.mean_z_m = np.sum(self.pop_vector["mcor_j"] * self.pop_vector["Z"]) / total_m

                self.m_young = self.pop_vector.loc[y_mask, "mcor_j"].sum()
                self.m_intermediate = self.pop_vector.loc[i_mask, "mcor_j"].sum()
                self.m_old = self.pop_vector.loc[o_mask, "mcor_j"].sum()

        # 5. Parse Synthetic Spectrum Table
        spec_rows = []
        if spec_start is not None:
            for line in lines[spec_start:]:
                tokens = line.strip().split()
                if len(tokens) >= 4:
                    try:
                        l_obs = float(tokens[0])
                        f_obs = float(tokens[1])
                        f_syn = float(tokens[2])
                        wei = float(tokens[3]) if tokens[3] != '*' else -1.0
                        spec_rows.append((l_obs, f_obs, f_syn, wei))
                    except ValueError:
                        continue

        if spec_rows:
            spec_arr = np.array(spec_rows)
            df_spec = pd.DataFrame(spec_arr, columns=["lambda", "f_obs", "f_syn", "weight"])
            df_spec["residual"] = df_spec["f_obs"] - df_spec["f_syn"]
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                df_spec["rel_res"] = np.where(df_spec["f_obs"] != 0, df_spec["residual"] / df_spec["f_obs"], 0.0)
            self.spectrum = df_spec

    def summary_dict(self):
        """Return scalar parameters as dictionary."""
        return {
            "file": self.filename,
            "chi2": self.chi2,
            "adev": self.adev,
            "snr": self.snr,
            "av": self.av,
            "v0": self.v0,
            "vd": self.vd,
            "mean_log_age_l": self.mean_log_age_l,
            "mean_log_age_m": self.mean_log_age_m,
            "mean_z_l": self.mean_z_l,
            "mean_z_m": self.mean_z_m,
            "x_young": self.x_young,
            "x_interm": self.x_intermediate,
            "x_old": self.x_old,
            "m_young": self.m_young,
            "m_interm": self.m_intermediate,
            "m_old": self.m_old,
            "mini_tot": self.mini_tot,
            "mcor_tot": self.mcor_tot,
        }


def parse_starlight_output(filepath):
    """Convenience helper function to parse .out file."""
    return StarlightOutput(filepath)


def batch_parse_starlight_outputs(out_files):
    """
    Parse a list of .out files and return a summary pandas DataFrame.
    """
    records = []
    for f in out_files:
        try:
            st = StarlightOutput(f)
            records.append(st.summary_dict())
        except Exception as e:
            records.append({"file": os.path.basename(f), "error": str(e)})
    return pd.DataFrame(records)
