''' A place for all the commands. '''

import os.path
import glob

def discover_commands():
    for path in glob.glob(os.path.dirname(__file__) + '/*.py'):
        if os.path.isfile(path):
            __import__('hexvi.commands.' + os.path.basename(path)[:-3])
