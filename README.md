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
- Support for large files
- Simple commands
- Color schemes
- Simple installation via `setuptools`
- Limited user configuration via `~/.config/hexvirc` and `~/.hexvirc`
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
    - <kbd>^</kbd>, <kbd>0</kbd>: move cursor to the start of display line
    - <kbd>$</kbd>: move cursor to the end of display line
    - <kbd>w</kbd>: move cursor to the next word
    - <kbd>b</kbd>: move cursor to the previous word
    - <kbd>PgUp</kbd>, <kbd>Shift+up</kbd>, <kbd>Ctrl+B</kbd>: previous page
    - <kbd>PgDown</kbd>, <kbd>Shift+down</kbd>, <kbd>Ctrl+F</kbd>: next page
    - <kbd>H</kbd>: jump to screen top
    - <kbd>M</kbd>: jump to screen middle
    - <kbd>L</kbd>: jump to screen bottom
- Text replacing (<kbd>r</kbd>)
- Text removal
    - <kbd>x</kbd>: remove character to the right
    - <kbd>*dec*</kbd><kbd>x</kbd>: remove *dec* characters to the right
    - <kbd>X</kbd>: remove character to the left
    - <kbd>*dec*</kbd><kbd>X</kbd>: remove *dec* characters to the left
    - <kbd>d</kbd> + all of the movement commands
- Search
    - forward search via <kbd>/</kbd>
    - backward search via <kbd>?</kbd>
    - PCRE regexes (examples: `a.*b`, `[\xF0-\xFF]`)
    - <kbd>n</kbd>: jump to next match
    - <kbd>N</kbd>: jump to previous match
    - <kbd>*dec*</kbd><kbd>n</kbd>: jump to *dec*-th next match
    - <kbd>*dec*</kbd><kbd>N</kbd>: jump to *dec*-th previous match

### Planned features

- File saving
- Multiple buffers (via tabs)
- Insert / append mode
- Undo/redo
- More movement commands (<kbd>t</kbd>, <kbd>f</kbd>, <kbd>T</kbd>,
  <kbd>F</kbd>)
- Easier jumps to offsets (`:deadbeef`, possibly
  <kbd>g</kbd><kbd>*hex*</kbd><kbd>CR</kbd>)
- Improved normal mode key retractions
- Command history (<kbd>↑</kbd>, <kbd>Ctrl+P</kbd>)
- Visual mode
- Yank/paste
- Search and replace
- Man page
- Enhanced control over appearance
- More built-in color schemes

### Features not likely to be added

- Support for marks
- <kbd>Tab</kbd> in command mode to auto complete input command
- <kbd>d/...</kbd>, <kbd>d?...</kbd> to delete up until searched text
- <kbd>Ctrl+R</kbd> in command mode to search command history
- <kbd>Ctrl+O</kbd> in normal mode to jump to last edit place, stack-based
