import unittest
import numpy as np
import os
from starlight_runner.preprocessing import (
    clean_spectrum, rebin_spectrum, deredden, apply_redshift,
    trim_spectral_bounds, varsmooth, varsmooth_error, downgrade_resolution
)
from starlight_runner.masking import SpectralMask
from starlight_runner.runner import StarlightConfig, generate_grid_files
from starlight_runner.parser import StarlightOutput
from starlight_runner.pylight_reader import starlightPars, popVectors, StSyntesis
from starlight_runner.montecarlo import (
    make_mc_spectra, generate_mc_grids, mc_config, load_mc_outputs, mc_statistics, mean_and_std,
    prepare_monte_carlo, cleanup_mc_spectra, error_spectrum_problem
)


class TestPreprocessing(unittest.TestCase):
    def test_clean_spectrum_dedup(self):
        wl = np.array([1000.0, 1000.0, 1001.0, 1002.0])
        flx = np.array([2.0, 4.0, 3.0, 5.0])
        eflx = np.array([1.0, 1.0, 0.5, 0.5])
        w_c, f_c, e_c = clean_spectrum(wl, flx, eflx)
        self.assertEqual(len(w_c), 3)
        self.assertAlmostEqual(w_c[0], 1000.0)
        self.assertAlmostEqual(f_c[0], 3.0)

    def test_rebin_spectrum(self):
        wl = np.linspace(5000, 6000, 500)
        flx = np.ones_like(wl) * 10.0
        eflx = np.ones_like(wl) * 1.0
        w_reb, f_reb, e_reb = rebin_spectrum(wl, flx, eflux=eflx, step=1.0)
        self.assertAlmostEqual(w_reb[1] - w_reb[0], 1.0)
        self.assertAlmostEqual(f_reb[0], 10.0, places=2)

    def test_deredden(self):
        wl = np.array([4000.0, 5500.0, 7000.0])
        flx = np.array([1.0, 1.0, 1.0])
        eflx = np.array([0.1, 0.1, 0.1])
        w_d, f_d, e_d = deredden(wl, flx, eflux=eflx, law="CCM", av=1.0, rv=3.1)
        self.assertTrue(f_d[0] > f_d[2])

    def test_downgrade_resolution_R(self):
        wl = np.linspace(5000, 6000, 1000)
        # Absorption line at 5500 A with sigma=1.0 A
        flx = 1.0 - 0.6 * np.exp(-0.5 * ((wl - 5500) / 1.0)**2)
        eflx = np.full_like(flx, 0.05)
        
        # Downgrade from R=5000 to R=1500
        w_s, f_s, e_s = downgrade_resolution(
            wl, flx, eflux=eflx, mode="R", val_ini=5000.0, val_target=1500.0
        )
        self.assertEqual(len(w_s), len(wl))
        # Absorption core must be shallower after convolution
        self.assertTrue(f_s.min() > flx.min())
        self.assertIsNotNone(e_s)

    def test_downgrade_resolution_sigma(self):
        wl = np.linspace(4000, 5000, 1000)
        flx = 1.0 - 0.5 * np.exp(-0.5 * ((wl - 4500) / 1.0)**2)
        w_s, f_s, _ = downgrade_resolution(
            wl, flx, mode="sigma", val_ini=30.0, val_target=120.0
        )
        self.assertTrue(f_s.min() > flx.min())

    def test_downgrade_resolution_fwhm(self):
        wl = np.linspace(6000, 7000, 1000)
        flx = 1.0 - 0.5 * np.exp(-0.5 * ((wl - 6500) / 1.0)**2)
        w_s, f_s, _ = downgrade_resolution(
            wl, flx, mode="FWHM", val_ini=1.0, val_target=3.0
        )
        self.assertTrue(f_s.min() > flx.min())

    def test_downgrade_resolution_vector_file(self):
        import tempfile
        wl = np.linspace(5000, 6000, 1000)
        flx = 1.0 - 0.6 * np.exp(-0.5 * ((wl - 5500) / 1.0)**2)
        
        # Test with 2-column resolution file (wavelength, R)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            tgt_file = f.name
            for w in np.linspace(4800, 6200, 50):
                f.write(f"{w:.1f} 1800.0\n")

        # Test with 1-column resolution file of len(lambda)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f_ini:
            ini_file = f_ini.name
            for _ in range(len(wl)):
                f_ini.write("5000.0\n")

        try:
            w_s, f_s, _ = downgrade_resolution(
                wl, flx, mode="R", file_ini=ini_file, file_target=tgt_file
            )
            self.assertEqual(len(w_s), len(wl))
            self.assertTrue(f_s.min() > flx.min())
        finally:
            if os.path.exists(tgt_file): os.remove(tgt_file)
            if os.path.exists(ini_file): os.remove(ini_file)


class TestMasking(unittest.TestCase):
    def test_mask_creation_and_json(self):
        sm = SpectralMask()
        sm.add_interval(6540.0, 6600.0, weight=0.0, name="Halpha")
        self.assertEqual(len(sm.intervals), 1)
        
        # Test preset
        opt = SpectralMask.from_preset("optical", wl_range=(4000, 7000))
        self.assertTrue(len(opt.intervals) > 0)


class TestParserAndReader(unittest.TestCase):
    def test_read_real_out_if_present(self):
        sample_out = "./synt/comb_major_2_clean.out"
        if os.path.exists(sample_out):
            out = StarlightOutput(sample_out)
            self.assertEqual(out.version, "V4")
            self.assertTrue(not np.isnan(out.chi2))
            
            pars, parlist, popin, popend, syntin, ver = starlightPars(sample_out)
            self.assertEqual(ver, "V4")
            self.assertTrue(len(pars) > 0)
            
            pop, popcomps = popVectors(sample_out)
            self.assertTrue(len(pop) > 0)
            
            spec = StSyntesis(sample_out)
            self.assertTrue(len(spec) > 0)


class TestMonteCarlo(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        lam = np.arange(4000.0, 4100.0, 1.0)
        self.flux = np.full(lam.size, 10.0)
        self.err = np.full(lam.size, 0.5)
        self.err[0] = 0.0  # unperturbed point
        self.spec = os.path.join(self.tmp, "gal.txt")
        np.savetxt(self.spec, np.column_stack([lam, self.flux, self.err]))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_make_mc_spectra(self):
        files = make_mc_spectra(self.spec, 50, out_dir=os.path.join(self.tmp, "a"), seed=3)
        self.assertEqual(len(files), 50)
        self.assertTrue(os.path.basename(files[0]).startswith("gal_mc0001"))
        sims = np.array([np.loadtxt(f) for f in files])
        np.testing.assert_allclose(sims[:, :, 0], np.broadcast_to(sims[0, :, 0], sims[:, :, 0].shape))
        np.testing.assert_allclose(sims[:, :, 2], np.broadcast_to(self.err, sims[:, :, 2].shape))
        self.assertTrue(np.all(sims[:, 0, 1] == 10.0))
        self.assertAlmostEqual(np.std(sims[:, 1:, 1]), 0.5, delta=0.05)
        # reproducible with the same seed
        again = make_mc_spectra(self.spec, 2, out_dir=os.path.join(self.tmp, "b"), seed=3)
        np.testing.assert_allclose(np.loadtxt(again[0]), sims[0])

    def test_make_mc_spectra_rejects_nan(self):
        d = np.loadtxt(self.spec)
        d[5, 1] = np.nan
        np.savetxt(self.spec, d)
        with self.assertRaises(ValueError):
            make_mc_spectra(self.spec, 2, out_dir=os.path.join(self.tmp, "a"))

    def test_mc_grid_uses_shared_mask(self):
        files = make_mc_spectra(self.spec, 3, out_dir=os.path.join(self.tmp, "a"), seed=1)
        cfg = mc_config(StarlightConfig(procs=1, out_dir=os.path.join(self.tmp, "out")),
                        os.path.dirname(files[0]), mask_file=os.path.join(self.tmp, "gal.mask"))
        grids = generate_mc_grids(files, cfg, mask_file="gal.mask", grid_dir=self.tmp)
        lines = open(grids[0]).read().splitlines()[15:]
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(l.split()[3] == "gal.mask" for l in lines))
        # MC grids must not be picked up by the normal "grid_*.inp" run
        import fnmatch
        self.assertFalse(any(fnmatch.fnmatch(os.path.basename(g), "grid_*.inp") for g in grids))

    def test_error_spectrum_problem(self):
        self.assertIsNone(error_spectrum_problem(self.spec))
        d = np.loadtxt(self.spec)
        two_col = os.path.join(self.tmp, "noerr.txt")
        np.savetxt(two_col, d[:, :2])
        self.assertIn("no error column", error_spectrum_problem(two_col))
        zero = os.path.join(self.tmp, "zeroerr.txt")
        np.savetxt(zero, np.column_stack([d[:, :2], np.zeros(len(d))]))
        self.assertIn("no positive errors", error_spectrum_problem(zero))
        with self.assertRaises(ValueError):
            make_mc_spectra(zero, 2, out_dir=os.path.join(self.tmp, "z"))

    def test_prepare_and_cleanup_in_mc_dir(self):
        mask = os.path.join(self.tmp, "gal.mask")
        open(mask, "w").write("0\n")
        mc_dir = os.path.join(self.tmp, "mcmc")
        job = prepare_monte_carlo(self.spec, StarlightConfig(procs=2), 4, mask_file=mask, mc_dir=mc_dir)
        self.assertEqual(job["root"], os.path.join(mc_dir, "gal"))
        self.assertEqual(len(os.listdir(job["spec_dir"])), 4)
        self.assertTrue(all(os.path.dirname(g) == job["root"] for g in job["grids"]))
        self.assertTrue(all(os.path.dirname(o) == job["out_dir"] for o in job["outs"]))
        cleanup_mc_spectra(job)
        self.assertFalse(os.path.exists(job["spec_dir"]))
        self.assertFalse(any(os.path.exists(g) for g in job["grids"]))

    def test_mean_and_std(self):
        vals = np.array([[1.0, 2.0], [3.0, np.nan], [5.0, 4.0]])
        mean, std, n = mean_and_std(vals)
        np.testing.assert_allclose(mean, [3.0, 3.0])
        np.testing.assert_allclose(std, [np.std([1.0, 3.0, 5.0]), np.std([2.0, 4.0])])
        np.testing.assert_array_equal(n, [3, 2])

    def test_mc_statistics_identical_fits(self):
        sample_out = "./synt/comb_major_6_clean.out"
        if not os.path.exists(sample_out):
            self.skipTest("sample .out not available")
        mc = load_mc_outputs([sample_out] * 3)
        self.assertEqual(mc["n"], 3)
        stats = mc_statistics(mc, {"BinPopVec": {"xo": [2e9, 2e10]}, "BinPopVecLab": ["xo"]})
        self.assertEqual(stats.at["xo", "N"], 3)
        self.assertEqual(stats.at["M*", "N"], 0)  # no distance -> NaN masses
        self.assertAlmostEqual(stats.at["xo", "std"], 0.0)
        self.assertGreater(stats.at["xo", "mean"], 0.0)



class TestCsvSpectra(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        self.csv = os.path.join(self.tmp, "gal.csv")
        with open(self.csv, "w") as fh:
            fh.write("wavelength,flux_mean,flux_err\n")
            for i in range(20):
                fh.write(f"{4000 + i:.1f},{1e-16 * (1 + i):.6e},{1e-17:.6e}\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_read_and_convert(self):
        from starlight_runner.spectrum_io import read_spectrum_table, needs_conversion
        self.assertTrue(needs_conversion(self.csv))
        d = read_spectrum_table(self.csv)
        self.assertEqual(d.shape, (20, 3))
        self.assertAlmostEqual(d[0, 0], 4000.0)

    def test_grid_uses_converted_spec(self):
        conv = os.path.join(self.tmp, "conv")
        cfg = StarlightConfig(obs_dir=self.tmp, out_dir=os.path.join(self.tmp, "out"), procs=1)
        grids = generate_grid_files([self.csv], cfg, output_dir=self.tmp, converted_dir=conv)
        text = open(grids[0]).read()
        self.assertIn("gal.spec ", text)
        data = np.loadtxt(os.path.join(conv, "gal.spec"))
        self.assertEqual(data.shape, (20, 3))

    def test_csv_without_errors_needs_err_flag_off(self):
        two = os.path.join(self.tmp, "two.csv")
        with open(two, "w") as fh:
            fh.write("wavelength,flux_mean\n4000,1e-16\n4001,2e-16\n")
        conv = os.path.join(self.tmp, "conv2")
        out = os.path.join(self.tmp, "out")
        with self.assertRaises(ValueError):
            generate_grid_files([two], StarlightConfig(out_dir=out, procs=1, is_err_available=1),
                                output_dir=self.tmp, converted_dir=conv)
        generate_grid_files([two], StarlightConfig(out_dir=out, procs=1, is_err_available=0),
                            output_dir=self.tmp, converted_dir=conv)

    def test_grid_quotes_config_in_subdir(self):
        cfg_dir = os.path.join(self.tmp, "cfg")
        os.makedirs(cfg_dir)
        for name in ("my.config", "MyBase"):
            open(os.path.join(cfg_dir, name), "w").close()
        cfg = StarlightConfig(out_dir=os.path.join(self.tmp, "out"), procs=1,
                              config_file=os.path.join(cfg_dir, "my.config"),
                              base_file=os.path.join(cfg_dir, "MyBase"))
        grids = generate_grid_files([self.csv], cfg, output_dir=self.tmp,
                                    converted_dir=os.path.join(self.tmp, "conv3"))
        line = open(grids[0]).read().splitlines()[-1].split()
        rel = os.path.relpath(cfg_dir).replace(os.sep, "/")
        self.assertEqual(line[1], f"'{rel}/my.config'")
        self.assertEqual(line[2], f"'{rel}/MyBase'")
        local = generate_grid_files([self.csv], StarlightConfig(out_dir=os.path.join(self.tmp, "out"), procs=1),
                                    output_dir=self.tmp, converted_dir=os.path.join(self.tmp, "conv4"))
        self.assertIn(" StCv04.C99.config BasesFile ", open(local[0]).read())

    def test_csv_without_errors_through_pipeline(self):
        from starlight_runner.preprocessing import preprocess_pipeline, ensure_error_array
        two = os.path.join(self.tmp, "noerr.csv")
        with open(two, "w") as fh:
            fh.write("wavelength,flux_mean\n")
            for i in range(30):
                fh.write(f"{4000 + i},{1e-16 * (1 + 0.01 * i):.6e}\n")
        e, has = ensure_error_array(np.ones(3), None)
        self.assertFalse(has)
        self.assertEqual(len(e), 3)
        out = os.path.join(self.tmp, "noerr.spec")
        wl, flx, eflx = preprocess_pipeline(two, output_spec_path=out, av=0.3, rebin_step=1.0)
        self.assertIsNone(eflx)
        self.assertEqual(np.loadtxt(out).shape[1], 2)  # placeholder error not saved

    def test_base_metallicities(self):
        from starlight_runner.runner import base_metallicities
        base = os.path.join(self.tmp, "MyBase")
        with open(base, "w") as fh:
            fh.write("4   [N_base]\n")
            fh.write("a.spec 1e9 0.02 a 1 0 0\nb.spec 1e9 0.004 b 1 0 0\n")
            fh.write("c.spec 1e10 0.02 c 1 0 0\nBB_800.dat 1.0 0.0000 bb 1 0 0\n")
            fh.write("# trailing comment 0.5\n")
        self.assertEqual(base_metallicities(base), [0.004, 0.02])
        self.assertEqual(base_metallicities(os.path.join(self.tmp, "missing")), [])

    def test_agn_nomenclature(self):
        from starlight_runner.pylight_reader import (
            agn_fc_exponent, agn_bb_temperature, is_agn_component, migrate_fc_bins, _component_values)
        self.assertEqual(agn_fc_exponent("agn_fc_0.25"), 0.25)
        self.assertEqual(agn_fc_exponent("AGN_FC_0.75"), 0.75)
        self.assertIsNone(agn_fc_exponent("age020_m42"))
        self.assertEqual(agn_bb_temperature("agn_bb_1200"), 1200.0)
        for c in ("agn_bb_800", "agn_fc_0.5", "BB_800.dat", "Power_125.dat", "PL_1"):
            self.assertTrue(is_agn_component(c), c)
        self.assertFalse(is_agn_component("logT7.7_MHm0.6_"))
        idx, vals = _component_values(["age020_m42", "agn_fc_0.25", "agn_fc_0.5", "agn_bb_800"], "fc")
        self.assertEqual(list(idx), [1, 2])
        self.assertEqual(list(vals), [0.25, 0.5])
        cfg = {"BinFCVecLab": ["FC1.25", "FC1.50", "FC1.75", "FCTot"], "BinFCVec": {}}
        self.assertTrue(migrate_fc_bins(cfg))
        self.assertEqual(cfg["BinFCVecLab"][0], "FC0.25")
        custom = {"BinFCVecLab": ["mine"], "BinFCVec": {"mine": [0, 2]}}
        self.assertFalse(migrate_fc_bins(custom))

    def test_script_roundtrip(self):
        from starlight_runner.scripting import generate_script, import_script, resolve_spectra
        state = {"exe": "star.exe", "obs_dir": "spectra", "spec_ext": "*.csv", "mask_dir": "mask",
                 "mask_ext": ".mask", "std_mask_enabled": True, "std_mask_file": "std.gm",
                 "config_file": "my.config", "base_dir": "BasesDir", "base_file": "Base.N",
                 "out_dir": "out", "fit_ini": 3700.0, "fit_fin": 6900.0, "llow_norm": 5650.0,
                 "lupp_norm": 5750.0, "kinematics": "FXK", "procs": 3, "is_err_available": 1,
                 "is_flag_available": 0, "seed": 42, "mc_enabled": True, "mc_n": 20,
                 "mc_dir": "mc", "mc_keep_spectra": True, "gal_dist": 12.5,
                 "pylight_config": {"IsAGNComp": False, "zsun": 0.02},
                 # Step 1 / Step 2
                 "z": 0.0123, "law": "Calzetti (2000 Starburst)", "av": 0.35, "rv": 4.05,
                 "rebin_step": 2.0, "trim_bounds_enabled": True, "trim_min": 3750.0, "trim_max": 6850.0,
                 "telluric_cuts": [{"low": 5360.0, "upp": 5380.0, "name": "spike"}],
                 "downgrade_res_enabled": True, "res_mode": 2, "res_ini": 2.5, "res_tgt": 6.0,
                 "res_ini_is_file": False, "res_tgt_is_file": False, "preprocessing_apply": True,
                 "masks": [{"low": 6550.0, "upp": 6580.0, "weight": 0.0, "name": "Ha"}]}
        script = os.path.join(self.tmp, "run.py")
        with open(script, "w") as fh:
            fh.write(generate_script(state, workdir_rel="."))
        got, warnings = import_script(script, gui_cwd=self.tmp)
        self.assertEqual(warnings, [])
        for k, v in state.items():
            if k != "pylight_config":
                self.assertEqual(got[k], v, k)
        self.assertEqual(got["l_norm"], 5700.0)
        self.assertEqual(got["pylight_config"]["zsun"], 0.02)
        # scripts kept in another folder: paths rebased to the GUI folder
        sub = os.path.join(self.tmp, "sub")
        got2, warnings2 = import_script(script, gui_cwd=sub)
        self.assertEqual(got2["obs_dir"], os.path.join("..", "spectra"))
        self.assertTrue(warnings2)
        # spectra resolution
        os.makedirs(os.path.join(self.tmp, "sp"))
        for n in ("b_2.csv", "b_10.csv", "b_1.csv", "x.mask"):
            open(os.path.join(self.tmp, "sp", n), "w").close()
        names = [os.path.basename(f) for f in resolve_spectra(os.path.join(self.tmp, "sp"), "*.csv")]
        self.assertEqual(names, ["b_1.csv", "b_2.csv", "b_10.csv"])

    def test_mc_from_csv(self):
        files = make_mc_spectra(self.csv, 2, out_dir=os.path.join(self.tmp, "mc"), seed=1)
        self.assertTrue(all(f.endswith(".spec") for f in files))
        self.assertIsNone(error_spectrum_problem(self.csv))

if __name__ == "__main__":
    unittest.main()
