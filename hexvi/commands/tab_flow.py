''' Commands related to tab management '''

import os
from hexvi.app_state import SearchState
from hexvi.command_registry import BaseCommand, BaseTabCommand

def _save(tab_manager, args, overwrite):
    if not tab_manager.current_tab:
        raise RuntimeError('No tab opened')
    filebuf = tab_manager.current_tab.file_buffer
    path = None
    if len(args):
        path = os.path.expanduser(args[0])
    if not path:
        path = filebuf.path
    if not path:
        raise RuntimeError('Need path')
    filebuf.save_to_file(path, overwrite)

class OpenTabCommand(BaseTabCommand):
    ''' Opens a new tab. '''
    names = ['tabe', 'tabedit', 'tabnew']

    def run(self, args):
        self._tab_manager.open_tab()

class PrevTabCommand(BaseTabCommand):
    ''' Navigates to the previous tab. '''
    names = ['tabp', 'tabprev']

    def run(self, args):
        self._tab_manager.cycle_tabs(SearchState.DIR_BACKWARD)

class NextTabCommand(BaseTabCommand):
    ''' Navigates to the next tab. '''
    names = ['tabn', 'tabnext']

    def run(self, args):
        self._tab_manager.cycle_tabs(SearchState.DIR_FORWARD)

class CloseActiveTabCommand(BaseCommand):
    ''' Close active tab. '''
    names = ['q', 'quit']

    def run(self, _args):
        self._tab_manager.close_current_tab()

class CloseActiveTabCommand(BaseCommand):
    ''' Close all tabs. '''
    names = ['qa', 'qall']

    def run(self, _args):
        while self._tab_manager.tabs:
            self._tab_manager.close_current_tab()

class TogglePaneCommand(BaseTabCommand):
    ''' Toggles the pane between hex and ascii dump. '''
    names = ['toggle_pane', 'toggle_panes']

    def run(self, args):
        if self.current_tab.pane == self.current_tab.PANE_HEX:
            self.current_tab.pane = self.current_tab.PANE_ASC
        else:
            self.current_tab.pane = self.current_tab.PANE_HEX

class SetPaneCommand(BaseTabCommand):
    ''' Sets the pane to either hex and ascii dump. '''
    names = ['set_pane', 'pane']

    def run(self, args):
        pane, = args
        if pane == 'hex':
            self.current_tab.pane = self.current_tab.PANE_HEX
        elif pane in ['ascii', 'asc']:
            self.current_tab.pane = self.current_tab.PANE_ASC
        else:
            raise RuntimeError('Bad pane (try with "hex" or "ascii")')

class OpenFileCommand(BaseTabCommand):
    ''' Opens a file located on HDD. '''
    names = ['e', 'edit']

    def run(self, args):
        path = args[0]
        self._tab_manager.open_in_current_tab(path)

class SaveFileCommand(BaseTabCommand):
    ''' Saves a file to a location on HDD bailing out if it exists. '''
    names = ['w', 'write']

    def run(self, args):
        _save(self._tab_manager, args, overwrite=False)

class ForceSaveFileCommand(BaseTabCommand):
    ''' Saves a file to a location on HDD overwriting it if it exists. '''
    names = ['w!', 'write!']

    def run(self, args):
        _save(self._tab_manager, args, overwrite=True)
