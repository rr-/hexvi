''' libreadline input emulation. '''

import re
import urwid

class ReadlineEdit(urwid.Edit):
    '''
    An urwid's Edit specialization that tries to emulate libreadline's
    capabilities. Extra useful when doing stuff in command mode.
    '''

    def __init__(self, *args, **kwargs):
        urwid.Edit.__init__(self, *args, multiline=False, **kwargs)
        self._bindings = {
            'ctrl b': self.move_to_prev_char,
            'ctrl f': self.move_to_next_char,
            'meta b': self.move_to_prev_word,
            'meta f': self.move_to_next_word,
            'ctrl a': self.move_to_start,
            'ctrl e': self.move_to_end,

            'ctrl w': self.kill_prev_word,
            'meta d': self.kill_next_word,
            'ctrl d': self.kill_next_char,
            'ctrl u': self.kill_all,
            'ctrl k': self.kill_all_ahead,

            'ctrl t': self.transpose_chars,
            'meta t': self.transpose_words,
        }

    def keypress(self, pos, key):
        if key in self._bindings:
            return self._bindings[key]()
        return super().keypress(pos, key)

    def move_to_prev_char(self):
        ''' Moves to the previous character. '''
        self.edit_pos -= 1

    def move_to_next_char(self):
        ''' Moves to the next character. '''
        self.edit_pos += 1

    def move_to_prev_word(self):
        ''' Moves to the start of the previous word. '''
        before, _ = self._kill_prev_word(self.edit_text, self.edit_pos)
        self.edit_pos = len(before)

    def move_to_next_word(self):
        ''' Moves to the start of the next word. '''
        before, after = self._kill_next_word(self.edit_text, self.edit_pos)
        self.edit_pos = len(before) + len(self.edit_text) - len(before + after)

    def move_to_start(self):
        ''' Moves to the start of line. '''
        self.edit_pos = 0

    def move_to_end(self):
        ''' Moves to the end of line. '''
        self.edit_pos = len(self.edit_text)

    def kill_next_char(self):
        ''' Deletes next character. '''
        before = self.edit_text[:self.edit_pos]
        after = self.edit_text[self.edit_pos:]
        self.edit_text = before + after[1:]

    def kill_prev_word(self):
        ''' Deletes previous word. '''
        before, after = self._kill_prev_word(self.edit_text, self.edit_pos)
        self.edit_text = before + after
        self.edit_pos = len(before)

    def kill_all(self):
        ''' Deletes everything. '''
        self.edit_text = ''
        self.edit_pos = 0

    def kill_all_ahead(self):
        ''' Deletes everything to the end of line. '''
        self.edit_text = self.edit_text[0:self.edit_pos]

    def kill_next_word(self):
        ''' Deletes next word. '''
        before, after = self._kill_next_word(self.edit_text, self.edit_pos)
        self.edit_text = before + after
        self.edit_pos = len(before)

    def transpose_chars(self):
        ''' Transposes characters to the left and to the right of the cursor. '''
        if len(self.edit_text) < 2:
            return
        if self.edit_pos == len(self.edit_text):
            self.edit_text = self.edit_text[:self.edit_pos-2] \
                + self.edit_text[self.edit_pos-1] \
                + self.edit_text[self.edit_pos-2] \
                + self.edit_text[self.edit_pos:]
        else:
            self.edit_text = self.edit_text[:self.edit_pos-1] \
                + self.edit_text[self.edit_pos-0] \
                + self.edit_text[self.edit_pos-1] \
                + self.edit_text[self.edit_pos+1:]
            self.edit_pos += 1

    def transpose_words(self):
        ''' Transposes words to the left and to the right of the cursor. '''
        words = re.split(r'(\W)', self.edit_text)
        words_before = []
        words_after = words+[]
        while len(''.join(words_before)) < self.edit_pos:
            words_before.append(words_after.pop(0))

        if words_after:
            if len(''.join(words_before)) == self.edit_pos:
                while re.match(r'\s+', words_after[0]):
                    words_before.append(words_after.pop(0))
                if words_after:
                    words_before.append(words_after.pop(0))

        word1_pos = len(words_before) - 1
        while word1_pos >= 0 and re.match(r'\s+', words[word1_pos]):
            word1_pos -= 1

        word2_pos = word1_pos - 1
        while word2_pos >= 0 and re.match(r'\s+', words[word2_pos]):
            word2_pos -= 1

        if word1_pos == -1 or word2_pos == -1:
            return

        words[word1_pos], words[word2_pos] = words[word2_pos], words[word1_pos]
        self.edit_text = ''.join(words)
        self.edit_pos = len(''.join(words_before))

    @staticmethod
    def _kill_prev_word(text, pos):
        before = text[:pos].rstrip(' ')
        after = text[pos:]
        if ' ' in before:
            before = before[0:before.rfind(' ')+1]
        else:
            before = ''
        return (before, after)

    @staticmethod
    def _kill_next_word(text, pos):
        before = text[:pos]
        after = text[pos:].lstrip(' ')
        if ' ' in after:
            after = after[after.find(' '):]
        else:
            after = ''
        return (before, after)
