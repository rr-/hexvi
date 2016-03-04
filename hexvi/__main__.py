#!/bin/python3
import os
import argparse
from .app_state import AppState
from .ui import Ui

def parse_args():
  parser = argparse.ArgumentParser(
    description='hexvi - a hex editor inspired by Vim.')
  parser.add_argument(metavar='FILE', dest='file', help='file to edit')
  return parser.parse_args()

def main():
  args = parse_args()
  app_state = AppState(args)
  ui = Ui(app_state)
  app_state.cmd_processor.exec(
    'source', os.path.join(app_state.resources_dir, 'hexvirc'))
  ui.run()

if __name__ == '__main__':
  main()
