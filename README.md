Hexvi - a hex editor inspired by Vim.
=====================================

### Installation

- Global: `sudo python setup.py install`
- Local:  `python setup.py install --local`

### Features

Note:

*dec* denotes any valid decimal number.  
*hex* denotes any valid hexadecimal number.

- Opening and displaying a file :)
- Flow
    - <kbd>Ctrl+W</kbd><kbd>Ctrl+W</kbd>, <kbd>Ctrl+W</kbd><kbd>W</kbd>, <kbd>Tab</kbd>: switch between hex and ASCII dump
    - <kbd>Ctrl+W</kbd><kbd>Ctrl+H</kbd>, <kbd>Ctrl+W</kbd><kbd>H</kbd>: switch to hex dump
    - <kbd>Ctrl+W</kbd><kbd>Ctrl+L</kbd>, <kbd>Ctrl+W</kbd><kbd>L</kbd>: switch to ASCII dump
    - <kbd>Ctrl+Q</kbd>: quit
- Movement
    - <kbd>h</kbd>, <kbd>←</kbd>: move cursor one character to the left
    - <kbd>l</kbd>, <kbd>→</kbd>: move cursor one character to the right
    - <kbd>j</kbd>, <kbd>↓</kbd>: move cursor down one display line
    - <kbd>k</kbd>, <kbd>↑</kbd>: move cursor up one display line
    - <kbd>*dec*</kbd><kbd>h</kbd>, <kbd>*dec*</kbd><kbd>←</kbd>: move cursor
      *dec* characters to the left
    - <kbd>*dec*</kbd><kbd>l</kbd>, <kbd>*dec*</kbd><kbd>→</kbd>: move cursor
      *dec* characters to the right
    - <kbd>*dec*</kbd><kbd>j</kbd>, <kbd>*dec*</kbd><kbd>↓</kbd>: move cursor
      down *dec* display lines
    - <kbd>*dec*</kbd><kbd>k</kbd>, <kbd>*dec*</kbd><kbd>↑</kbd>: move cursor
      up *dec* display lines
    - <kbd>g</kbd><kbd>g</kbd>: move cursor to the beginning of the file
    - <kbd>G</kbd>: move cursor to the end of file
    - <kbd>*hex*</kbd><kbd>G</kbd>: move cursor to the *hex* offset
    - <kbd>^</kbd>: move cursor to the start of display line
    - <kbd>$</kbd>: move cursor to the end of display line
- Search
    - forward search via <kbd>/</kbd>
    - backward search via <kbd>?</kbd>
    - PCRE regexes (examples: `a.*b`, `[\xF0-\xFF]`)
    - <kbd>n</kbd>: jump to next match
    - <kbd>N</kbd>: jump to previous match
    - <kbd>*dec*</kbd><kbd>n</kbd>: jump to *dec*-th next match
    - <kbd>*dec*</kbd><kbd>N</kbd>: jump to *dec*-th previous match
- Simple commands
- Color schemes
- User configuration via `~/.config/hexvirc` and `~/.hexvirc`
- Simple installation via `setuptools`
- Support for large files (for now)

### Planned features

- Multiple buffers (via tabs)
- Visual mode
- Yank/paste
- Editing documents (this is going to make large file support tough)
    - Inserting, replacing and deleting text
    - Search and replace
    - Undo/redo
- Increase control over appearance
- Offer more built-in color schemes
