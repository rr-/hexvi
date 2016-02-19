from setuptools import setup, find_packages

setup(
    name             = 'hexvi',
    description      = 'A hex editor inspired by Vim.',
    author           = 'rr-',
    author_email     = 'rr-@sakuya.pl',
    url              = 'https://github.com/rr-/hexvi',
    license          = 'MIT',

    packages         = find_packages(),
    package_data     = {'': ['data/*']},

    entry_points     = {
        'console_scripts': [
            'hexvi = hexvi.__main__:main',
        ],
    },

    install_requires = ['urwid', 'zope.event'],
    keywords         = ['hex editor', 'console', 'urwid', 'desktop'],
)
