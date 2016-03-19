''' A place for all the commands. '''

import os.path
import glob
MODULES = glob.glob(os.path.dirname(__file__) + '/*.py')
for path in MODULES:
    if os.path.isfile(path):
        __import__('hexvi.commands.' + os.path.basename(path)[:-3])
