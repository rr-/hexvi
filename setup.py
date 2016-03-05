from setuptools import setup, find_packages
import os

data_files = []
for root, dirs, files in os.walk('hexvi/share'):
  data_files.append((root, list(os.path.join(root, file) for file in files)))

setup(
    name             = 'hexvi',
    description      = 'A hex editor inspired by Vim.',
    author           = 'rr-',
    author_email     = 'rr-@sakuya.pl',
    url              = 'https://github.com/rr-/hexvi',
    license          = 'MIT',

    packages         = find_packages(),
    data_files       = data_files,

    entry_points     = {
        'console_scripts': [
            'hexvi = hexvi.__main__:main',
        ],
    },

    install_requires = ['urwid', 'regex'],
    keywords         = ['hex editor', 'console', 'urwid', 'desktop'],
)
