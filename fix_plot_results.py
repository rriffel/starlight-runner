gui_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(gui_path, "r", encoding="utf-8") as f:
    gcontent = f.read()

import re

# Find the _plot_results function block
start_idx = gcontent.find("    def _plot_results(self):")
end_idx = gcontent.find("    def _on_export_figures(self):", start_idx)

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
        import numpy as np
        mask_idx = wei <= 0.0
        if np.any(mask_idx):
            ax_top.scatter(l_obs[mask_idx], f_obs[mask_idx], color="#94A3B8", s=6, label="Masked (w=0)")

        ax_top.set_ylabel("Flux (Normalized)", fontsize=11)
        
        # We need chi2 and adev to show in title
        chi2 = 0; adev = 0
        for i, p in enumerate(data['ParList']):
            if 'chi2/Nl_eff' in p or 'chi2]' in p: chi2 = data['pars'][i]
            if 'adev' in p: adev = data['pars'][i]
            
        ax_top.set_title(f"STARLIGHT Fit: {filename} ($\chi^2$={chi2:.2f}, adev={adev:.2f}%)", fontsize=12, fontweight="bold")
        ax_top.legend(loc="upper right", frameon=True)
        ax_top.grid(True, linestyle="--", alpha=0.4)

        # Residuals Plot
        ax_res.plot(l_obs, residual, color="#2563EB", lw=1.0)
        ax_res.axhline(0, color="#64748B", linestyle="--", lw=1.0)
        ax_res.set_xlabel("Wavelength ($\AA$)", fontsize=11)
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
            
            m_young = np.sum(m_vals[age_yr <= 1.0e8])
            m_interm = np.sum(m_vals[(age_yr > 1.0e8) & (age_yr <= 2.0e9)])
            m_old = np.sum(m_vals[age_yr > 2.0e9])
            ax_pop_m.set_title(f"Mass SFH (Young={m_young:.1f}%, Interm={m_interm:.1f}%, Old={m_old:.1f}%)", fontsize=11)
            
            ax_pop_m.grid(True, linestyle="--", alpha=0.4)

        self.canvas_results.draw()

"""

gcontent = gcontent[:start_idx] + new_plot + gcontent[end_idx:]

# Also fix the summary dict export in _on_export_table because parsed_output is now a dict
old_export = """        if out_path:
            df = pd.DataFrame([self.parsed_output.summary_dict()])
            df.to_csv(out_path, index=False)"""

new_export = """        if out_path:
            import pandas as pd
            # Make a simple dict out of pars
            out_d = {'file': self.parsed_output['filename']}
            for i, p in enumerate(self.parsed_output['ParList']):
                out_d[p] = self.parsed_output['pars'][i]
            df = pd.DataFrame([out_d])
            df.to_csv(out_path, index=False)"""
gcontent = gcontent.replace(old_export, new_export)

with open(gui_path, "w", encoding="utf-8") as f:
    f.write(gcontent)

