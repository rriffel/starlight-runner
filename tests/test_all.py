import unittest
import numpy as np
import os
from starlight_runner.preprocessing import clean_spectrum, rebin_spectrum, deredden, apply_redshift, trim_spectral_bounds
from starlight_runner.masking import SpectralMask
from starlight_runner.runner import StarlightConfig, generate_grid_files
from starlight_runner.parser import StarlightOutput
from starlight_runner.pylight_reader import starlightPars, popVectors, StSyntesis


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


if __name__ == "__main__":
    unittest.main()
