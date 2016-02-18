Hexvi - a hex editor inspired by Vim.
=====================================

# Features

- Opening and displaying a file :)
- Movement

    *dec* denotes any valid decimal number.  
    *hex* denotes any valid hexadecimal number.

    - <kbd>Tab</kbd>: switch between hex and ASCII dump
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

# Planned features

- Colon commands
- Multiple buffers (via tabs)
- Search
- Yank/paste
- Editing documents
- Search and replace
- `.hexvirc`
- Neat appearance
