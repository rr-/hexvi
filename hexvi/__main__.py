#!/bin/python3
import argparse
import os
import sys
from hexvi.app_state import AppState
from hexvi.settings import Settings
from hexvi.ui import Ui

def parse_args():
  parser = argparse.ArgumentParser(
    description='hexvi - a hex editor inspired by Vim.')
  parser.add_argument(metavar='FILE', dest='file', help='file to edit')
  return parser.parse_args()

def main():
  args = parse_args()
  settings = Settings()
  app_state = AppState(settings, args)
  ui = Ui(app_state)
  app_state.cmd_processor.exec(
    'source', os.path.join(app_state.resources_dir, 'hexvirc'))
  for p in ['~/.hexvirc', '~/.config/hexvirc']:
    if os.path.exists(os.path.expanduser(p)):
      app_state.cmd_processor.exec('source', p)
  ui.run()

if __name__ == '__main__':
  main()
