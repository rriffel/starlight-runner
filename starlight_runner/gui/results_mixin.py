"""Auto-generated mixin module for Starlight Runner GUI."""
import sys, os, glob, json, re, traceback
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from . import constants

from ..pylight_reader import (
    starlightPars, popVectors, StSyntesis, pylight_properties, format_pylight_value,
    agn_fc_exponent, agn_bb_temperature
)
from ..montecarlo import load_mc_outputs, mc_statistics, mean_and_std, write_mc_table
from ..custom_widgets import PylightConfigDialog

class ResultsMixin:
    def _create_step4_results(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left control / Metrics panel
        left_panel = QWidget()
        left_panel.setFixedWidth(380)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # File Select
        grp_out = QGroupBox("1. Select Starlight Fit (.out)")
        f_out = QVBoxLayout(grp_out)
        btn_open_out = QPushButton("Open Result(s) (.out)")
        btn_open_out.setToolTip("Select one fit, or several fits of the same spectrum\n"
                                "(Monte Carlo realizations) to show mean ± std.")
        btn_open_out.clicked.connect(self._on_open_out_dialog)
        self.lbl_out_file = QLabel("No fit loaded")
        self.lbl_out_file.setProperty("role", "mutedLabel")
        self.lbl_out_file.setStyleSheet("font-size: 11px;")
        f_out.addWidget(btn_open_out)
        f_out.addWidget(self.lbl_out_file)
        left_layout.addWidget(grp_out)

        # Metric Summary Cards
        grp_metrics = QGroupBox("2. Fit Metrics & Physical Properties")
        f_met = QFormLayout(grp_metrics)
        self.lbl_chi2 = QLabel("—")
        self.lbl_adev = QLabel("—")
        self.lbl_snr = QLabel("—")
        self.lbl_av = QLabel("—")
        self.lbl_v0 = QLabel("—")
        self.lbl_vd = QLabel("—")
        self.lbl_age_l = QLabel("—")
        self.lbl_age_m = QLabel("—")
        self.lbl_z_l = QLabel("—")
        self.lbl_z_m = QLabel("—")

        f_met.addRow("Reduced χ²:", self.lbl_chi2)
        f_met.addRow("adev (%):", self.lbl_adev)
        f_met.addRow("S/N in Window:", self.lbl_snr)
        f_met.addRow("Dust A_V (mag):", self.lbl_av)
        f_met.addRow("Velocity v_0 (km/s):", self.lbl_v0)
        f_met.addRow("Dispersion σ_d (km/s):", self.lbl_vd)
        f_met.addRow("⟨log t_*⟩_L (yr):", self.lbl_age_l)
        f_met.addRow("⟨log t_*⟩_M (yr):", self.lbl_age_m)
        f_met.addRow("⟨Z_*⟩_L (Z_sun):", self.lbl_z_l)
        f_met.addRow("⟨Z_*⟩_M (Z_sun):", self.lbl_z_m)
        left_layout.addWidget(grp_metrics)

        # Galaxy Distance input (needed for M* / SFR in V4 files)
        grp_dist = QGroupBox("Galaxy Distance")
        f_dist = QHBoxLayout(grp_dist)
        f_dist.addWidget(QLabel("D (Mpc):"))
        self.sb_gal_dist = QDoubleSpinBox()
        self.sb_gal_dist.setRange(0, 1e6)
        self.sb_gal_dist.setDecimals(4)
        self.sb_gal_dist.setValue(0.0)
        self.sb_gal_dist.setToolTip(
            "Galaxy distance in Mpc.\n"
            "For V5 files this is auto-filled from LumDistInMpc.\n"
            "For V4 files you must set it manually to get correct M* and SFR."
        )
        f_dist.addWidget(self.sb_gal_dist)
        left_layout.addWidget(grp_dist)

        # Pylight Configuration
        grp_config = QGroupBox("3. Pylight Configuration")
        f_config = QVBoxLayout(grp_config)
        btn_config = QPushButton("Open Configuration Editor...")
        btn_config.setMinimumHeight(40)
        btn_config.clicked.connect(self._open_pylight_config)
        f_config.addWidget(btn_config)
        left_layout.addWidget(grp_config)

        # Export Buttons
        btn_save_plot = QPushButton("Export Plots (PNG/PDF)")
        btn_save_plot.clicked.connect(self._on_export_figures)
        left_layout.addWidget(btn_save_plot)

        btn_save_table = QPushButton("Export Table (.csv)")
        btn_save_table.clicked.connect(self._on_export_table)
        left_layout.addWidget(btn_save_table)

        left_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(360)
        scroll_area.setMaximumWidth(500)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(left_panel)

        # Right Plots
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.fig_results = Figure(figsize=(9, 8), constrained_layout=True)
        self.canvas_results = FigureCanvas(self.fig_results)
        self.toolbar_results = NavigationToolbar(self.canvas_results, self)

        right_layout.addWidget(self.toolbar_results)
        right_layout.addWidget(self.canvas_results)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(scroll_area)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        return page

    def _open_pylight_config(self):
        if hasattr(self, '_sync_pylight_zs'):
            self._sync_pylight_zs()  # Zs from the Step 3 Base File
        dlg = PylightConfigDialog(self, self.pylight_config)
        if dlg.exec_() == QDialog.Accepted:
            self.pylight_config = dlg.config
            self._plot_results()
            self.statusBar().showMessage("Plots updated with new configuration.")

    def _on_open_out_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Open STARLIGHT Output(s)", "", "Starlight Output (*.out);;All Files (*)"
        )
        if len(files) == 1:
            self.load_starlight_out(files[0])
        elif len(files) > 1:
            self.load_mc_set(files)

    def load_starlight_out(self, filepath):
        self.results_files = [filepath]  # reopened by Load Config / Load Script
        try:
            # Use the PyLight standard reader
            pars, ParList, popin, popend, syntin, version = starlightPars(filepath)
            pop, popComps = popVectors(filepath)
            spec = StSyntesis(filepath)

            # Save raw arrays so _plot_results and _on_export_table can use them
            self.parsed_output = {
                'pars': pars,
                'ParList': ParList,
                'pop': pop,
                'popComps': popComps,
                'spec': spec,
                'filename': os.path.basename(filepath),
                'version': version,
            }
            self.lbl_out_file.setText(os.path.basename(filepath))

            # Map parameters by name from ParList
            def get_par(name):
                for i, p in enumerate(ParList):
                    if name in p: return pars[i]
                return np.nan

            chi2 = get_par('chi2/Nl_eff')
            if np.isnan(chi2): chi2 = get_par('chi2]')
            adev = get_par('adev')
            snr = get_par('S/N in S/N window')
            av = get_par('AV_min')
            v0 = get_par('v0_min')
            vd = get_par('vd_min')

            # Store version-specific parameters for CSV export
            if version == 'V5':
                fobs_norm = get_par('fobs_norm')
                lum_dist = get_par('LumDistInMpc')
                Mini_t = get_par('Mini_tot')
                Mcor_t = get_par('Mcor_tot')
                self.parsed_output['fobs_norm'] = fobs_norm
                self.parsed_output['Mini_t'] = Mini_t
                self.parsed_output['Mcor_t'] = Mcor_t
                self.parsed_output['LumDistInMpc'] = lum_dist
                # Auto-fill distance for V5 files
                if not np.isnan(lum_dist) and lum_dist > 0:
                    self.sb_gal_dist.setValue(lum_dist)
            else:  # V4
                fobs_norm = get_par('fobs_norm (in input units)')
                Mini_tot = get_par('Mini_tot')
                Mcor_tot = get_par('Mcor_tot')
                self.parsed_output['fobs_norm'] = fobs_norm
                self.parsed_output['Mini_tot_raw'] = Mini_tot
                self.parsed_output['Mcor_tot_raw'] = Mcor_tot

            # Calculate mean ages and metallicities from pop arrays
            # pop columns: 0=x_j(%), 1=Mini_j(%), 2=Mcor_j(%), 3=age_j(yr), 4=Z_j, 5=(L/M)_j, 6=j
            # AGN components always have Z = 0: means sum stellar populations only.
            # Light: weights are fractions of the TOTAL light (FC included) -- not
            # renormalized to the stellar light. Mass: AGN components have no mass.
            stellar = pop[:, 4] > 0
            x_j = pop[stellar, 0]
            mcor_j = pop[stellar, 2]
            age_yr = pop[stellar, 3]
            log_age = np.log10(np.where(age_yr > 0, age_yr, 1))
            Z_j = pop[stellar, 4]

            tot_x = np.sum(pop[:, 0])
            tot_m = np.sum(mcor_j)

            mean_log_age_l = np.sum(x_j * log_age) / tot_x if tot_x > 0 else np.nan
            mean_z_l = np.sum(x_j * Z_j) / tot_x if tot_x > 0 else np.nan

            mean_log_age_m = np.sum(mcor_j * log_age) / tot_m if tot_m > 0 else np.nan
            mean_z_m = np.sum(mcor_j * Z_j) / tot_m if tot_m > 0 else np.nan

            # Update Labels
            self.lbl_chi2.setText(f"{chi2:.3f}" if not np.isnan(chi2) else "—")
            self.lbl_adev.setText(f"{adev:.2f}%" if not np.isnan(adev) else "—")
            self.lbl_snr.setText(f"{snr:.1f}" if not np.isnan(snr) else "—")
            self.lbl_av.setText(f"{av:.3f}" if not np.isnan(av) else "—")
            self.lbl_v0.setText(f"{v0:.1f}" if not np.isnan(v0) else "—")
            self.lbl_vd.setText(f"{vd:.1f}" if not np.isnan(vd) else "—")
            self.lbl_age_l.setText(f"{mean_log_age_l:.2f}" if not np.isnan(mean_log_age_l) else "—")
            self.lbl_age_m.setText(f"{mean_log_age_m:.2f}" if not np.isnan(mean_log_age_m) else "—")
            self.lbl_z_l.setText(f"{mean_z_l:.4f}" if not np.isnan(mean_z_l) else "—")
            self.lbl_z_m.setText(f"{mean_z_m:.4f}" if not np.isnan(mean_z_m) else "—")

            self._plot_results()
            self.statusBar().showMessage(f"Loaded fit: {os.path.basename(filepath)}")
        except Exception as e:
            QMessageBox.critical(self, "Error Reading .out File", str(e))

    # -----------------------------------------------------------------
    # Monte Carlo uncertainties
    # -----------------------------------------------------------------

    def load_mc_set(self, files):
        """Load N fits of the same galaxy and show mean ± error of every quantity."""
        self.results_files = list(files)  # reopened by Load Config / Load Script
        try:
            mc = load_mc_outputs(files)
        except Exception as e:
            QMessageBox.critical(self, "Error Reading Monte Carlo Fits", str(e))
            return
        if mc['n'] < 2:
            QMessageBox.warning(self, "Monte Carlo", "At least two readable fits are needed.")
            return
        base = re.sub(r"_mc\d+$", "", os.path.splitext(os.path.basename(mc['files'][0]))[0])
        self.parsed_output = {
            'pars': mc['pars'][0],
            'ParList': mc['ParList'],
            'pop': mc['pop'][0],
            'popComps': mc['popComps'],
            'spec': mc['spec'][0],
            'filename': f"{base}_mc.out",
            'version': mc['version'],
            'mc': mc,
        }
        self.lbl_out_file.setText(f"{base}: {mc['n']} Monte Carlo fits")
        self._update_mc_labels()
        self._plot_results()
        msg = f"Loaded {mc['n']} Monte Carlo fits of {base}"
        if mc['skipped']:
            msg += f" ({len(mc['skipped'])} skipped)"
        self.statusBar().showMessage(msg)

    def _update_mc_labels(self):
        mc = self.parsed_output['mc']
        stats = mc_statistics(mc, self.pylight_config, self.sb_gal_dist.value())

        def show(lbl, key, fmt):
            if key not in stats.index or np.isnan(stats.at[key, 'mean']):
                lbl.setText("—")
                return
            lbl.setText(f"{stats.at[key, 'mean']:{fmt}} ± {stats.at[key, 'std']:{fmt}}")

        show(self.lbl_chi2, 'ChiSqrt', '.3f')
        show(self.lbl_adev, 'Adev', '.2f')
        show(self.lbl_snr, 'SNR', '.1f')
        show(self.lbl_av, 'Av', '.3f')
        show(self.lbl_v0, 'v0', '.1f')
        show(self.lbl_vd, 'vd', '.1f')
        show(self.lbl_age_l, 'Mage_L', '.2f')
        show(self.lbl_age_m, 'Mage_M', '.2f')
        show(self.lbl_z_l, 'MZ_L', '.4f')
        show(self.lbl_z_m, 'MZ_M', '.4f')

    def _plot_results(self):
        self.fig_results.clear()
        if self.parsed_output is None:
            self.canvas_results.draw()
            return

        data = self.parsed_output
        spec = data['spec']
        pop = data['pop']
        filename = data['filename']
        
        if len(spec) == 0:
            self.canvas_results.draw()
            return

        config = self.pylight_config

        # Monte Carlo sets: every plotted quantity is computed per realization and
        # shown as the mean with the std of the N fits as error bar; single fits have no bars.
        mc = data.get('mc')
        err_kw = dict(ecolor='#334155', elinewidth=1.0, capsize=2)

        def _norm(v):
            return v * (100.0 / np.sum(v)) if np.sum(v) > 0 else v

        runs = [(_norm(p[:, 0]), _norm(p[:, 2])) for p in (mc['pop'] if mc else [pop])]

        def agg(fn):
            """fn(x_j, mu_j) of each run -> (mean, error or None)."""
            vals = np.array([fn(x, m) for x, m in runs], dtype=float)
            if not mc:
                return vals[0], None
            mean, std, _ = mean_and_std(vals, axis=0)
            return mean, std

        # Determine number of bottom subplots based on AGN flags
        plot_fc = config.get("IsAGNComp", False) or config.get("OnlyFC", False)
        plot_hd = config.get("IsAGNComp", False) and not config.get("OnlyFC", False)
        
        n_cols = 3 + (1 if plot_fc else 0) + (1 if plot_hd else 0)
        gs = self.fig_results.add_gridspec(3, n_cols, height_ratios=[2.5, 1.0, 2.0], hspace=0.3, wspace=0.15)
            
        ax_top = self.fig_results.add_subplot(gs[0, :])
        ax_res = self.fig_results.add_subplot(gs[1, :], sharex=ax_top)
        
        ax_pop_all = self.fig_results.add_subplot(gs[2, 0])
        ax_pop_z = self.fig_results.add_subplot(gs[2, 1], sharey=ax_pop_all)
        ax_pop_bin = self.fig_results.add_subplot(gs[2, 2], sharey=ax_pop_all)
        
        ax_agn_fc = None
        ax_agn_hd = None
        curr_col = 3
        
        if plot_fc:
            ax_agn_fc = self.fig_results.add_subplot(gs[2, curr_col], sharey=ax_pop_all)
            curr_col += 1
            
        if plot_hd:
            ax_agn_hd = self.fig_results.add_subplot(gs[2, curr_col], sharey=ax_pop_all)

        # Common styling for plots
        axes_to_style = [ax_top, ax_res, ax_pop_all, ax_pop_z, ax_pop_bin]
        if ax_agn_fc: axes_to_style.append(ax_agn_fc)
        if ax_agn_hd: axes_to_style.append(ax_agn_hd)
        
        for ax in axes_to_style:
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, linestyle=":", alpha=0.6)

        # Columns for StSyntesis: 0:l_obs, 1:f_obs, 2:f_syn, 3:wei
        l_obs = spec[:, 0]
        wei = spec[:, 3]
        if mc:
            specs = np.array(mc['spec'], dtype=float)
            f_obs = np.nanmean(specs[:, :, 1], axis=0)
            f_syn, e_syn, _ = mean_and_std(specs[:, :, 2], axis=0)
            residual = np.nanmean(specs[:, :, 1] - specs[:, :, 2], axis=0)
        else:
            f_obs = spec[:, 1]
            f_syn = spec[:, 2]
            residual = f_obs - f_syn

        # Top Plot: Observed vs Synthetic
        if mc:
            ax_top.plot(l_obs, f_obs, color="#0F172A", lw=1.1, label=f"Observed (mean of {mc['n']})")
            ax_top.fill_between(l_obs, f_syn - e_syn, f_syn + e_syn, color="#DC2626", alpha=0.3, lw=0)
            ax_top.plot(l_obs, f_syn, color="#DC2626", lw=1.3, label="Synthetic (mean ± std)")
        else:
            ax_top.plot(l_obs, f_obs, color="#0F172A", lw=1.1, label="Observed")
            ax_top.plot(l_obs, f_syn, color="#DC2626", lw=1.3, label="Synthetic")

        # Flag masked points with continuous lines
        mask_regions = np.where(wei <= 0.0)[0]
        segments = []
        if len(mask_regions) > 0:
            segments = np.split(mask_regions, np.where(np.diff(mask_regions) != 1)[0] + 1)
        if config.get("pltmask", False):
            mask_regions = np.where(wei <= 0.0)[0]
            if len(mask_regions) > 0:
                segments = np.split(mask_regions, np.where(np.diff(mask_regions) != 1)[0] + 1)
                for idx, seg in enumerate(segments):
                    lbl = "Masked" if idx == 0 else None
                    ax_top.plot(l_obs[seg], f_obs[seg], color="cyan", lw=1.5, label=lbl, zorder=3)

        ax_top.set_ylabel("Normalized Flux", fontsize=11, fontweight='normal')
        
        chi2 = 0; adev = 0; av = 0; snr = 0
        for i, p in enumerate(data['ParList']):
            if 'chi2/Nl_eff' in p or 'chi2]' in p: chi2 = data['pars'][i]
            if 'adev' in p: adev = data['pars'][i]
            if 'AV_min' in p: av = data['pars'][i]
            if 'S/N' in p: snr = data['pars'][i]
            
        if mc:
            title = (f"{os.path.splitext(filename)[0]} — Monte Carlo: mean of N = {mc['n']} fits "
                     "(errors: std)")
        else:
            title = filename
        ax_top.set_title(title, fontsize=12, fontweight="bold", pad=10)
        ax_top.legend(loc="upper right", frameon=True, facecolor='white', edgecolor='#E2E8F0', fancybox=True)

        # Residuals Plot
        ax_res.plot(l_obs, residual, color="#1E293B", lw=1.0)
        
        # Plot mask on residuals too
        if config.get("pltmask", False):
            if len(mask_regions) > 0:
                for seg in segments:
                    ax_res.plot(l_obs[seg], residual[seg], color="cyan", lw=1.5, zorder=3)
                    
        ax_res.axhline(0, color="#3B82F6", linestyle="--", lw=1.2)
        ax_res.set_xlabel(r"Wavelength ($\AA$)", fontsize=11, fontweight='normal')
        ax_res.set_ylabel("Residual", fontsize=10, fontweight='normal')

        if len(pop) > 0:
            age_yr = pop[:, 3]
            Z_j = pop[:, 4]

            # Plot 1: ax_pop_all (Sum of all metallicities)
            ax_pop_all.set_xlim(5, 10.5)
            ax_pop_all.set_ylim(0, 100)
            ax_pop_all.set_xlabel('log Age (yr)', fontsize=10)
            ax_pop_all.set_ylabel('Fraction (%)', fontsize=10)
            
            unique_ages = np.unique(age_yr)
            sum_x, e_sum_x = agg(lambda x, m: [np.sum(x[age_yr == a]) for a in unique_ages])
            sum_m, e_sum_m = agg(lambda x, m: [np.sum(m[age_yr == a]) for a in unique_ages])
            log_ages = np.log10(np.where(unique_ages > 0, unique_ages, 1))
            
            ax_pop_all.bar(log_ages, sum_x, width=0.4, align='center', color='#3B82F6', alpha=0.35, edgecolor='#1D4ED8', lw=1.2, label=r'$\Sigma x_j$ (Light)',
                           yerr=e_sum_x, error_kw=err_kw)
            ax_pop_all.bar(log_ages, sum_m, width=0.2, align='center', color='None', edgecolor='#991B1B', lw=1.5, ls='dotted', label=r'$\Sigma \mu_j$ (Mass)',
                           yerr=e_sum_m, error_kw=dict(err_kw, ecolor='#991B1B'))
            ax_pop_all.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='#E2E8F0', fontsize=9)
            ax_pop_all.set_title("Summed Populations", fontsize=11, fontweight="bold", pad=8)

            # Plot 2: ax_pop_z (Fractions by Metallicity)
            ax_pop_z.set_xlim(5, 10.5)
            ax_pop_z.set_ylim(0, 100)
            ax_pop_z.set_xlabel('log Age (yr)', fontsize=10)
            ax_pop_z.set_yticks([])
            ax_pop_z.spines['left'].set_visible(False)
            
            # metallicities of the base (Step 3 Base File); if they do not
            # match this fit's components, use the ones in the .out itself
            zs = np.asarray(config.get('Zs') or [], dtype=float)
            zs = zs[zs > 0]  # Z = 0 is always AGN, never a stellar metallicity
            matches = zs.size and np.isclose(Z_j[:, None], zs[None, :], rtol=1e-4, atol=0).any()
            if not matches:
                zs = np.unique(Z_j[Z_j > 0])
            zscolor = ['#EF4444', '#D946EF', '#3B82F6', '#0F172A', '#06B6D4', '#10B981', '#F59E0B']
            zswidth = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
            zsun = config.get('zsun', 0.0152)
            
            c = 0
            p_y = 100
            for z in zs:
                mask = np.isclose(Z_j, z, rtol=1e-4, atol=0)
                if not np.any(mask): continue
                color = zscolor[c % len(zscolor)]
                width = zswidth[c % len(zswidth)]
                
                a_z = age_yr[mask]
                log_a_z = np.log10(np.where(a_z > 0, a_z, 1))
                z_x, e_z_x = agg(lambda x, m: x[mask])
                z_m, e_z_m = agg(lambda x, m: m[mask])
                ax_pop_z.bar(log_a_z, z_x, width=width, align='center', color=color, alpha=0.35, edgecolor=color, lw=1.2,
                             yerr=e_z_x, error_kw=dict(err_kw, ecolor=color))
                ax_pop_z.bar(log_a_z, z_m, width=width/2.0, align='center', color='None', edgecolor=color, lw=1.5, ls='dotted',
                             yerr=e_z_m, error_kw=dict(err_kw, ecolor=color))
                
                p_y -= 12
                if p_y > 27:
                    ax_pop_z.text(5.2, p_y, f"{z/zsun:.2f} Z_sun", fontsize=9, color=color, fontweight='normal')
                c += 1
            
            ax_pop_z.set_title("Fractions by Metallicity", fontsize=11, fontweight="bold", pad=8)

            # Plot 3: ax_pop_bin (Binned vectors)
            ax_pop_bin.set_xlim(5, 10.5)
            ax_pop_bin.set_ylim(0, 100)
            ax_pop_bin.set_xlabel('log Age (yr)', fontsize=10)
            ax_pop_bin.set_yticks([])
            ax_pop_bin.spines['left'].set_visible(False)
            
            bin_pop_vec = config.get('BinPopVec', {})
            bin_labels = config.get('BinPopVecLab', list(bin_pop_vec.keys()))
            
            macolor = ['#3B82F6', '#D946EF', '#EF4444', '#0F172A', '#06B6D4', '#10B981', '#F59E0B']
            c = 0
            p_y = 100
            for label in bin_labels:
                if label not in bin_pop_vec: continue
                bounds = bin_pop_vec[label]
                mask = (age_yr > bounds[0]) & (age_yr <= bounds[1])
                b_x, e_b_x = agg(lambda x, m: np.sum(x[mask]))
                b_m, e_b_m = agg(lambda x, m: np.sum(m[mask]))
                b_center = (np.log10(max(bounds[0], 1)) + np.log10(bounds[1])) / 2.0
                
                color = macolor[c % len(macolor)]
                ax_pop_bin.bar(b_center, b_x, width=0.4, align='center', color=color, alpha=0.35, edgecolor=color, lw=1.2,
                               yerr=e_b_x, error_kw=dict(err_kw, ecolor=color))
                ax_pop_bin.bar(b_center, b_m, width=0.2, align='center', color='None', edgecolor=color, lw=1.5, ls='dotted',
                               yerr=e_b_m, error_kw=dict(err_kw, ecolor=color))
                
                p_y -= 12
                if p_y > 27:
                    ax_pop_bin.text(5.2, p_y, label, fontsize=9, color=color, fontweight='normal')
                c += 1
            
            ax_pop_bin.set_title("Binned Vectors", fontsize=11, fontweight="bold", pad=8)

            if plot_fc or plot_hd:
                nu, fc_idx = [], []
                bb, bb_idx = [], []
                popComps = data.get('popComps', [])
                
                # agn_fc_<alpha> / agn_bb_<T> (same rules as pylight_reader / urutau)
                for i, comp in enumerate(popComps):
                    alpha = agn_fc_exponent(comp)
                    temp = agn_bb_temperature(comp)
                    if alpha is not None:
                        nu.append(alpha)
                        fc_idx.append(i)
                    elif temp is not None:
                        bb.append(temp)
                        bb_idx.append(i)
                        
                if ax_agn_fc:
                    ax_agn_fc.spines['left'].set_visible(False)
                    ax_agn_fc.set_yticks([])
                    if len(nu) > 0:
                        fc_x, e_fc_x = agg(lambda x, m: x[fc_idx])
                        ax_agn_fc.bar(nu, fc_x, width=0.1, align='center', color='#8B5CF6', alpha=0.5, edgecolor='#6D28D9',
                                      yerr=e_fc_x, error_kw=dict(err_kw, ecolor='#6D28D9'))
                    ax_agn_fc.set_title('FC', fontsize=11, fontweight="bold", pad=8)
                    ax_agn_fc.set_xlabel(r'Index $\alpha$', fontsize=10)
                    
                if ax_agn_hd:
                    ax_agn_hd.spines['left'].set_visible(False)
                    ax_agn_hd.set_yticks([])
                    if len(bb) > 0:
                        bb_x, e_bb_x = agg(lambda x, m: x[bb_idx])
                        ax_agn_hd.bar(bb, bb_x, width=50, align='center', color='#F59E0B', alpha=0.5, edgecolor='#B45309',
                                      yerr=e_bb_x, error_kw=dict(err_kw, ecolor='#B45309'))
                    ax_agn_hd.set_title('Hot Dust', fontsize=11, fontweight="bold", pad=8)
                    ax_agn_hd.set_xlabel('T (K)', fontsize=10)

        self.canvas_results.draw()

    def _on_export_figures(self):
        if self.parsed_output is None:
            QMessageBox.warning(self, "No Fit Loaded", "Please load a .out file first.")
            return

        filename = self.parsed_output.get('filename', 'fit.out') if isinstance(self.parsed_output, dict) else getattr(self.parsed_output, 'filename', 'fit.out')
        base_name = os.path.splitext(filename)[0]

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Figure", f"{base_name}_fit.png",
            "PNG Image (*.png);;PDF Document (*.pdf);;SVG Vector (*.svg);;All Files (*)"
        )
        if out_path:
            try:
                self.fig_results.savefig(out_path, dpi=200, bbox_inches='tight')
                QMessageBox.information(self, "Figure Saved", f"Saved: {out_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error Saving Figure", f"Failed to save figure:\n{str(e)}")

    def _on_export_table(self):
        """Export CSV with all pylight-derived quantities, matching the original pylight.py output format."""
        if self.parsed_output is None:
            QMessageBox.warning(self, "No Fit Loaded", "Please load a .out file first.")
            return

        data = self.parsed_output
        filename = data.get('filename', 'fit.out')
        base_name = os.path.splitext(filename)[0]
        config = self.pylight_config
        version = data.get('version', 'V4')

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Parameters Table",
            f"{base_name}_props.csv" if 'mc' in data else f"{base_name}_summary.csv",
            "CSV Table (*.csv);;TXT Table (*.txt);;All Files (*)"
        )
        if not out_path:
            return

        try:
            gal_D = self.sb_gal_dist.value()
            if 'mc' in data:
                # Monte Carlo set: mean and error (std_) of the N fits
                stats = mc_statistics(data['mc'], config, gal_D)
                write_mc_table(stats, out_path, name=base_name, pylight_config=config)
            else:
                props = pylight_properties(data['pars'], data['ParList'], data['pop'],
                                           data.get('popComps', np.array([])), version, config, gal_D)
                out_d = {'File': filename}
                out_d.update({k: format_pylight_value(k, v, config) for k, v in props.items()})
                df = pd.DataFrame([out_d])
                if out_path.endswith('.txt'):
                    df.to_csv(out_path, sep='\t', index=False)
                else:
                    df.to_csv(out_path, index=False)

            QMessageBox.information(self, "Table Saved", f"Saved: {out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Table", f"Failed to save table:\n{str(e)}\n{traceback.format_exc()}")


