#!/bin/python3

'''
The CLI facade. Argument parsing and core lifetime management goes here.
'''

import argparse
import os
import hexvi.events as events
from hexvi.app_state import AppState
from hexvi.command_processor import CommandProcessor
from hexvi.tab_manager import TabManager
from hexvi.settings import Settings
from hexvi.ui import Ui

def parse_args():
    parser = argparse.ArgumentParser(
        description='hexvi - a hex editor inspired by Vim.')
    parser.add_argument(metavar='FILE', dest='file', help='file to edit')
    return parser.parse_args()

def main():
    anything_printed = False
    def print_message_handler(evt):
        nonlocal anything_printed
        anything_printed = True
        print(evt.message)
    events.register_handler(events.PrintMessage, print_message_handler)

    # basic initialization
    args = parse_args()
    settings = Settings()
    app_state = AppState(settings, args)
    tab_manager = TabManager(app_state)
    cmd_processor = CommandProcessor(app_state, tab_manager)

    user_interface = Ui(tab_manager, cmd_processor, app_state)

    # initial configuration
    cmd_processor.exec(
        'source', os.path.join(app_state.resources_dir, 'hexvirc'))
    for path in ['~/.hexvirc', '~/.config/hexvirc']:
        if os.path.exists(os.path.expanduser(path)):
            cmd_processor.exec('source', path)

    try:
        tab_manager.open_tab(args.file)
    except Exception as ex:
        tab_manager.open_tab()
        events.notify(events.PrintMessage(str(ex), style='msg-error'))

    # print collected messages, if any
    events.unregister_handler(events.PrintMessage, print_message_handler)
    if anything_printed:
        input('Press Enter to continue...')

    user_interface.run()

if __name__ == '__main__':
    main()
