import argparse
import numpy as np
from pathlib import Path
import sys


def get_args():
    parser = argparse.ArgumentParser(description='WAVE Maker')
    parser.add_argument('file', metavar='File', type=str, nargs=1, help='WAVE file to work on')
    parser.add_argument('-c', metavar='Comp', type=int, nargs='?', const=1, help='Compression format (1 is PCM and default)')

    return parser.parse_args()


def make_header(fmt, sample_rate, bits_per_sample, n_channels, n_samples):
    chunk_size = None
    if fmt == 1:
        chunk_size = 36 + (n_samples * n_channels * bits_per_sample // 8)
    else:
        sys.exit('Non-PCM compression not yet implemented')

    header = bytes('RIFF', 'ascii')
    header += chunk_size.to_bytes(length=4, byteorder='little')
    header += bytes('WAVE', 'ascii')
    header += bytes('fmt ', 'ascii')
    header += int(16).to_bytes(length=4, byteorder='little')


def main():
    args = vars(get_args())


if __name__ == '__main__':
    main()

