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
from toStarlight import creatStarlightInputs
Logo()



################################# Exemple of use of starlightMask ################################

#creatStarlightInputs('ConfigToStarlight_HrPypop')
#creatStarlightInputs('ConfigToStarlight_NIR_PyHR')
#creatStarlightInputs('ConfigToStarlight_NIR')
creatStarlightInputs('ConfigToStarlight')
