import re
import urwid

class ReadlineEdit(urwid.Edit):
    def __init__(self, *args, **kwargs):
        urwid.Edit.__init__(self, *args, multiline=False, **kwargs)

    def keypress(self, pos, key):
        if key == 'ctrl b': return self.move_to_prev_char()
        if key == 'ctrl f': return self.move_to_next_char()
        if key == 'meta b': return self.move_to_prev_word()
        if key == 'meta f': return self.move_to_next_word()
        if key == 'ctrl a': return self.move_to_start()
        if key == 'ctrl e': return self.move_to_end()

        if key == 'ctrl w': return self.kill_prev_word()
        if key == 'meta d': return self.kill_next_word()
        if key == 'ctrl d': return self.kill_next_char()
        if key == 'ctrl u': return self.kill_all()
        if key == 'ctrl k': return self.kill_all_ahead()

        if key == 'ctrl t': return self.transpose_chars()
        if key == 'meta t': return self.transpose_words()

        return super().keypress(pos, key)

    def move_to_prev_char(self):
        self.edit_pos -= 1

    def move_to_next_char(self):
        self.edit_pos += 1

    def move_to_prev_word(self):
        before, after = self._kill_prev_word(self.edit_text, self.edit_pos)
        self.edit_pos = len(before)

    def move_to_next_word(self):
        before, after = self._kill_next_word(self.edit_text, self.edit_pos)
        self.edit_pos = len(before) + len(self.edit_text) - len(before+after)

    def move_to_start(self):
        self.edit_pos = 0

    def move_to_end(self):
        self.edit_pos = len(self.edit_text)

    def kill_next_char(self):
        before = self.edit_text[:self.edit_pos]
        after = self.edit_text[self.edit_pos:]
        self.edit_text = before + after[1:]

    def kill_prev_word(self):
        before, after = self._kill_prev_word(self.edit_text, self.edit_pos)
        self.edit_text = before + after
        self.edit_pos = len(before)

    def kill_all(self):
        self.edit_text = ''
        self.edit_pos = 0

    def kill_all_ahead(self):
        self.edit_text = self.edit_text[0:self.edit_pos]

    def kill_next_word(self):
        before, after = self._kill_next_word(self.edit_text, self.edit_pos)
        self.edit_text = before + after
        self.edit_pos = len(before)

    def transpose_chars(self):
        if len(self.edit_text) < 2:
            return
        if self.edit_pos == len(self.edit_text):
            self.edit_text = (self.edit_text[:self.edit_pos-2]
                + self.edit_text[self.edit_pos-1]
                + self.edit_text[self.edit_pos-2]
                + self.edit_text[self.edit_pos:])
        else:
            self.edit_text = (self.edit_text[:self.edit_pos-1]
                + self.edit_text[self.edit_pos-0]
                + self.edit_text[self.edit_pos-1]
                + self.edit_text[self.edit_pos+1:])
            self.edit_pos += 1

    def transpose_words(self):
        words = re.split('(\W)', self.edit_text)
        words_before = []
        words_after = words+[]
        while len(''.join(words_before)) < self.edit_pos:
            words_before.append(words_after.pop(0))

        if words_after:
            if len(''.join(words_before)) == self.edit_pos:
                while re.match('\s+', words_after[0]):
                    words_before.append(words_after.pop(0))
                if words_after:
                    words_before.append(words_after.pop(0))

        word1_pos = len(words_before) - 1
        while word1_pos >= 0 and re.match('\s+', words[word1_pos]):
            word1_pos -= 1

        word2_pos = word1_pos - 1
        while word2_pos >= 0 and re.match('\s+', words[word2_pos]):
            word2_pos -= 1

        if word1_pos == -1 or word2_pos == -1:
            return

        words[word1_pos], words[word2_pos] = words[word2_pos], words[word1_pos]
        self.edit_text = ''.join(words)
        self.edit_pos = len(''.join(words_before))

    def _kill_prev_word(self, text, pos):
        before = text[:pos].rstrip(' ')
        after = text[pos:]
        if ' ' in before:
            before = before[0:before.rfind(' ')+1]
        else:
            before = ''
        return (before, after)

    def _kill_next_word(self, text, pos):
        before = text[:pos]
        after = text[pos:].lstrip(' ')
        if ' ' in after:
            after = after[after.find(' '):]
        else:
            after = ''
        return (before, after)
