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
    prepare_monte_carlo, cleanup_mc_spectra
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


if __name__ == "__main__":
    unittest.main()
