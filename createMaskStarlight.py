#!/usr/bin/python
import os, glob
from pylab import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from scipy import interpolate
import re
import time
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import imp
import gc
from PyPopStarsLogo import Logo
from matplotlib import pyplot as plt
from CreateMasks import starlightMask
Logo()



################################# Exemple of use of starlightMask ################################

files = glob.glob('*.spec')


for f in files:
     makemask=starlightMask(f,'mask_'+re.sub('.spec','.mask',f),False, False)

