import re
import sys

gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

# Add imports for ReadStarlightParameters
if "from ReadStarlightParameters import" not in gcontent:
    gcontent = gcontent.replace("import sys\n", "import sys\nimport os\nsys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))\nfrom ReadStarlightParameters import starlightPars, popVectors, StSyntesis\n")

# Replace load_starlight_out
old_load = """    def load_starlight_out(self, filepath):
        try:
            st = StarlightOutput(filepath)
            self.parsed_output = st
            self.lbl_out_file.setText(os.path.basename(filepath))

            # Update Labels
            self.lbl_chi2.setText(f"{st.chi2:.3f}" if not np.isnan(st.chi2) else "—")
            self.lbl_adev.setText(f"{st.adev:.2f}%" if not np.isnan(st.adev) else "—")
            self.lbl_snr.setText(f"{st.snr:.1f}" if not np.isnan(st.snr) else "—")
            self.lbl_av.setText(f"{st.av:.3f}" if not np.isnan(st.av) else "—")
            self.lbl_v0.setText(f"{st.v0:.1f}" if not np.isnan(st.v0) else "—")
            self.lbl_vd.setText(f"{st.vd:.1f}" if not np.isnan(st.vd) else "—")
            self.lbl_age_l.setText(f"{st.mean_log_age_l:.2f}" if not np.isnan(st.mean_log_age_l) else "—")
            self.lbl_age_m.setText(f"{st.mean_log_age_m:.2f}" if not np.isnan(st.mean_log_age_m) else "—")
            self.lbl_z_l.setText(f"{st.mean_z_l:.4f}" if not np.isnan(st.mean_z_l) else "—")
            self.lbl_z_m.setText(f"{st.mean_z_m:.4f}" if not np.isnan(st.mean_z_m) else "—")

            self._plot_results()
            self.statusBar().showMessage(f"Loaded fit: {os.path.basename(filepath)}")
        except Exception as e:
            QMessageBox.critical(self, "Error Reading .out File", str(e))"""

new_load = """    def load_starlight_out(self, filepath):
        try:
            # Use the PyLight standard reader
            pars, ParList, popin, popend, syntin, version = starlightPars(filepath)
            pop, popComps = popVectors(filepath)
            spec = StSyntesis(filepath)
            
            # Save raw arrays so _plot_results can use them
            self.parsed_output = {
                'pars': pars,
                'ParList': ParList,
                'pop': pop,
                'popComps': popComps,
                'spec': spec,
                'filename': os.path.basename(filepath)
            }
            self.lbl_out_file.setText(os.path.basename(filepath))

            # Map parameters by name from ParList
            # ParList in V5 is e.g., ['[chi2/Nl_eff', 'chi2]', 'flux_unit]', 'fobs_norm', 'Lobs_norm', 'LumDistInMpc', '[adev (%)]', ...]
            # We find the indices dynamically
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

            # Calculate mean ages and metallicities from pop arrays
            # pop columns: 0=x_j(%), 1=Mini_j(%), 2=Mcor_j(%), 3=age_j(yr), 4=Z_j, 5=(L/M)_j, 6=j
            x_j = pop[:, 0]
            mcor_j = pop[:, 2]
            age_yr = pop[:, 3]
            log_age = np.log10(np.where(age_yr > 0, age_yr, 1))
            Z_j = pop[:, 4]
            
            tot_x = np.sum(x_j)
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
            QMessageBox.critical(self, "Error Reading .out File", str(e))"""

gcontent = gcontent.replace(old_load, new_load)

# Replace _plot_results
old_plot = """    def _plot_results(self):
        self.fig_results.clear()
        if self.parsed_output is None or self.parsed_output.spectrum.empty:
            self.canvas_results.draw()
            return

        st = self.parsed_output
        df_spec = st.spectrum

        # 2 Subplots: Top = Spectrum Fit & Residuals; Bottom = Population Vectors (x_j & m_j)
        gs = self.fig_results.add_gridspec(3, 2, height_ratios=[2.5, 1.0, 1.8], hspace=0.3)
        ax_top = self.fig_results.add_subplot(gs[0, :])
        ax_res = self.fig_results.add_subplot(gs[1, :], sharex=ax_top)
        ax_pop_x = self.fig_results.add_subplot(gs[2, 0])
        ax_pop_m = self.fig_results.add_subplot(gs[2, 1])

        # Top Plot: Observed vs Synthetic
        ax_top.plot(df_spec["lambda"], df_spec["f_obs"], color="#0F172A", lw=1.1, label="Observed")
        ax_top.plot(df_spec["lambda"], df_spec["f_syn"], color="#DC2626", lw=1.3, label="STARLIGHT Synthetic")

        # Flag masked points in gray
        masked_pts = df_spec[df_spec["weight"] <= 0.0]
        if not masked_pts.empty:
            ax_top.scatter(masked_pts["lambda"], masked_pts["f_obs"], color="#94A3B8", s=6, label="Masked (w=0)")

        ax_top.set_ylabel("Flux (Normalized)", fontsize=11)
        ax_top.set_title(f"STARLIGHT Fit: {st.filename} " + r"($\chi^2$" + f"={st.chi2:.2f}, adev={st.adev:.2f}%, " + r"$A_V$" + f"={st.av:.2f})", fontsize=12, fontweight="bold")
        ax_top.legend(loc="upper right", frameon=True)

        ax_top.grid(True, linestyle="--", alpha=0.4)

        # Residuals Plot
        ax_res.plot(df_spec["lambda"], df_spec["residual"], color="#2563EB", lw=1.0)
        ax_res.axhline(0, color="#64748B", linestyle="--", lw=1.0)
        ax_res.set_xlabel(r"Wavelength ($\AA$)", fontsize=11)
        ax_res.set_ylabel("Resid (O-S)", fontsize=10)
        ax_res.grid(True, linestyle="--", alpha=0.4)

        # Bottom Left: Light Fractions (x_j)
        if not st.pop_vector.empty:
            pv = st.pop_vector
            ages = pv["log_age"].to_numpy()
            x_vals = pv["x_j"].to_numpy()
            m_vals = pv["mcor_j"].to_numpy()

            ax_pop_x.bar(np.arange(len(x_vals)), x_vals, color="#3B82F6", edgecolor="#1D4ED8", width=0.7)
            ax_pop_x.set_ylabel("Light Fraction x_j (%)", fontsize=10)
            ax_pop_x.set_xlabel("SSP Index", fontsize=10)
            ax_pop_x.set_title(f"Light SFH (Young={st.x_young:.1f}%, Interm={st.x_intermediate:.1f}%, Old={st.x_old:.1f}%)", fontsize=11)
            ax_pop_x.grid(True, linestyle="--", alpha=0.4)

            # Bottom Right: Mass Fractions (m_j)
            ax_pop_m.bar(np.arange(len(m_vals)), m_vals, color="#10B981", edgecolor="#047857", width=0.7)
            ax_pop_m.set_ylabel("Mass Fraction m_j (%)", fontsize=10)
            ax_pop_m.set_xlabel("SSP Index", fontsize=10)
            ax_pop_m.set_title("Mass SFH", fontsize=11)
            ax_pop_m.grid(True, linestyle="--", alpha=0.4)

        self.canvas_results.draw()"""

new_plot = """    def _plot_results(self):
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

        # 2 Subplots: Top = Spectrum Fit & Residuals; Bottom = Population Vectors (x_j & m_j)
        gs = self.fig_results.add_gridspec(3, 2, height_ratios=[2.5, 1.0, 1.8], hspace=0.3)
        ax_top = self.fig_results.add_subplot(gs[0, :])
        ax_res = self.fig_results.add_subplot(gs[1, :], sharex=ax_top)
        ax_pop_x = self.fig_results.add_subplot(gs[2, 0])
        ax_pop_m = self.fig_results.add_subplot(gs[2, 1])

        # Columns for StSyntesis: 0:l_obs, 1:f_obs, 2:f_syn, 3:wei
        l_obs = spec[:, 0]
        f_obs = spec[:, 1]
        f_syn = spec[:, 2]
        wei = spec[:, 3]
        
        residual = f_obs - f_syn

        # Top Plot: Observed vs Synthetic
        ax_top.plot(l_obs, f_obs, color="#0F172A", lw=1.1, label="Observed")
        ax_top.plot(l_obs, f_syn, color="#DC2626", lw=1.3, label="STARLIGHT Synthetic")

        # Flag masked points in gray
        mask_idx = wei <= 0.0
        if np.any(mask_idx):
            ax_top.scatter(l_obs[mask_idx], f_obs[mask_idx], color="#94A3B8", s=6, label="Masked (w=0)")

        ax_top.set_ylabel("Flux (Normalized)", fontsize=11)
        
        # We need chi2 and adev to show in title
        chi2 = 0; adev = 0
        for i, p in enumerate(data['ParList']):
            if 'chi2/Nl_eff' in p or 'chi2]' in p: chi2 = data['pars'][i]
            if 'adev' in p: adev = data['pars'][i]
            
        ax_top.set_title(f"STARLIGHT Fit: {filename} " + r"($\chi^2$" + f"={chi2:.2f}, adev={adev:.2f}%)", fontsize=12, fontweight="bold")
        ax_top.legend(loc="upper right", frameon=True)
        ax_top.grid(True, linestyle="--", alpha=0.4)

        # Residuals Plot
        ax_res.plot(l_obs, residual, color="#2563EB", lw=1.0)
        ax_res.axhline(0, color="#64748B", linestyle="--", lw=1.0)
        ax_res.set_xlabel(r"Wavelength ($\AA$)", fontsize=11)
        ax_res.set_ylabel("Resid (O-S)", fontsize=10)
        ax_res.grid(True, linestyle="--", alpha=0.4)

        # Bottom Left: Light Fractions (x_j)
        if len(pop) > 0:
            x_vals = pop[:, 0]
            m_vals = pop[:, 2]

            ax_pop_x.bar(np.arange(len(x_vals)), x_vals, color="#3B82F6", edgecolor="#1D4ED8", width=0.7)
            ax_pop_x.set_ylabel("Light Fraction x_j (%)", fontsize=10)
            ax_pop_x.set_xlabel("SSP Index", fontsize=10)
            
            # Simple Age fractions logic
            age_yr = pop[:, 3]
            x_young = np.sum(x_vals[age_yr <= 1.0e8])
            x_interm = np.sum(x_vals[(age_yr > 1.0e8) & (age_yr <= 2.0e9)])
            x_old = np.sum(x_vals[age_yr > 2.0e9])
            
            ax_pop_x.set_title(f"Light SFH (Young={x_young:.1f}%, Interm={x_interm:.1f}%, Old={x_old:.1f}%)", fontsize=11)
            ax_pop_x.grid(True, linestyle="--", alpha=0.4)

            # Bottom Right: Mass Fractions (m_j)
            ax_pop_m.bar(np.arange(len(m_vals)), m_vals, color="#10B981", edgecolor="#047857", width=0.7)
            ax_pop_m.set_ylabel("Mass Fraction m_j (%)", fontsize=10)
            ax_pop_m.set_xlabel("SSP Index", fontsize=10)
            ax_pop_m.set_title("Mass SFH", fontsize=11)
            ax_pop_m.grid(True, linestyle="--", alpha=0.4)

        self.canvas_results.draw()"""

gcontent = gcontent.replace(old_plot, new_plot)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

