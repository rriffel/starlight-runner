import re

file_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/runner.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

def_pad = """    b_dir = _to_rel_dir(config.base_dir)
    o_dir = _to_rel_dir(config.obs_dir)
    m_dir = _to_rel_dir(config.mask_dir)
    s_dir = _to_rel_dir(config.out_dir)

    def _pad(val, comment, min_width=40):
        s_val = str(val)
        # Ensure at least 4 spaces
        spaces = max(4, min_width - len(s_val))
        return f"{s_val}{' ' * spaces}{comment}\\n\""""

old_setup = """    b_dir = _to_rel_dir(config.base_dir)
    o_dir = _to_rel_dir(config.obs_dir)
    m_dir = _to_rel_dir(config.mask_dir)
    s_dir = _to_rel_dir(config.out_dir)"""

content = content.replace(old_setup, def_pad)

old_writes = """            f.write(f"{b_dir:<40} [base_dir]\\n")
            f.write(f"{o_dir:<40} [obs_dir]\\n")
            f.write(f"{m_dir:<40} [mask_dir]\\n")
            f.write(f"{s_dir:<40} [out_dir]\\n")
            f.write(f"{config.seed:<40} [your phone number]\\n")
            f.write(f"{config.llow_sn:<40.1f} [llow_SN]   lower-lambda of S/N window\\n")
            f.write(f"{config.lupp_sn:<40.1f} [lupp_SN]   upper-lambda of S/N window\\n")
            f.write(f"{config.olsyn_ini:<40.1f} [Olsyn_ini] lower-lambda for fit\\n")
            f.write(f"{config.olsyn_fin:<40.1f} [Olsyn_fin] upper-lambda for fit\\n")
            f.write(f"{config.delta_lamb:<40.1f} [Odlsyn]    delta-lambda for fit\\n")
            f.write(f"{config.fscale_chi2:<40.1f} [fscale_chi2] fudge-factor for chi2\\n")
            f.write(f"{config.kinematics:<40} [FIT/FXK] Fit or Fix kinematics\\n")
            f.write(f"{config.is_err_available:<40} [IsErrSpecAvailable]  1/0 = Yes/No\\n")
            f.write(f"{config.is_flag_available:<40} [IsFlagSpecAvailable] 1/0 = Yes/No\\n")"""

new_writes = """            f.write(_pad(b_dir, "[base_dir]"))
            f.write(_pad(o_dir, "[obs_dir]"))
            f.write(_pad(m_dir, "[mask_dir]"))
            f.write(_pad(s_dir, "[out_dir]"))
            f.write(_pad(config.seed, "[your phone number]"))
            f.write(_pad(f"{config.llow_sn:.1f}", "[llow_SN]   lower-lambda of S/N window"))
            f.write(_pad(f"{config.lupp_sn:.1f}", "[lupp_SN]   upper-lambda of S/N window"))
            f.write(_pad(f"{config.olsyn_ini:.1f}", "[Olsyn_ini] lower-lambda for fit"))
            f.write(_pad(f"{config.olsyn_fin:.1f}", "[Olsyn_fin] upper-lambda for fit"))
            f.write(_pad(f"{config.delta_lamb:.1f}", "[Odlsyn]    delta-lambda for fit"))
            f.write(_pad(f"{config.fscale_chi2:.1f}", "[fscale_chi2] fudge-factor for chi2"))
            f.write(_pad(config.kinematics, "[FIT/FXK] Fit or Fix kinematics"))
            f.write(_pad(config.is_err_available, "[IsErrSpecAvailable]  1/0 = Yes/No"))
            f.write(_pad(config.is_flag_available, "[IsFlagSpecAvailable] 1/0 = Yes/No"))"""

content = content.replace(old_writes, new_writes)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Runner patched with padding!")
