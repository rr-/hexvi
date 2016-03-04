#!/bin/python3
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
  Ui(app_state).run()

if __name__ == '__main__':
  main()
