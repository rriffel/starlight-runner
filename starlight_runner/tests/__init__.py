import unittest
import os
from .test_all import *

def run_tests():
    """Run all unit tests for the starlight_runner package."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('starlight_runner.tests.test_all')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()
