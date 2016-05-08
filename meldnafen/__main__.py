import argparse

from meldnafen import start_meldnafen


parser = argparse.ArgumentParser()
parser.add_argument('--debug', '-d', action='store_true', default=False)
opts = parser.parse_args()

start_meldnafen(**vars(opts))
