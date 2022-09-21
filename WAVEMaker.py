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
    """Generates Header and Format chunks"""
    chunk_size = None
    if fmt == 1:  # PCM
        chunk_size = 36 + (n_samples * n_channels * bits_per_sample // 8)
        header = bytes('RIFF', 'ascii')                                                                         # 0     RIFF Chunk ID
        header += chunk_size.to_bytes(length=4, byteorder='little')                                             # 4     Filesize - 8
        header += bytes('WAVE', 'ascii')                                                                        # 8     Format code (WAVE)
        header += bytes('fmt ', 'ascii')                                                                        # 12    Format Chunk ID
        header += int(16).to_bytes(length=4, byteorder='little')                                                # 16    Format Chunk Size (16 for PCM)
        header += fmt.to_bytes(length=2, byteorder='little')                                                    # 20    Format Code (1 for PCM)
        header += n_channels.to_bytes(length=2, byteorder='little')                                             # 22    Number of channels
        header += sample_rate.to_bytes(length=4, byteorder='little')                                            # 24    Sample rate
        header += (sample_rate * n_channels * bits_per_sample // 8).to_bytes(length=4, byteorder='little')      # 28    Byte rate
        header += (n_channels * bits_per_sample // 8).to_bytes(length=2, byteorder='little')                    # 32    Block allign: The number of bytes for one sample across all channels
        header += bits_per_sample.to_bytes(length=2, byteorder='little')                                        # 34    Bits per sample

    else:
        sys.exit('Non-PCM compression not yet implemented')


def main():
    args = vars(get_args())


if __name__ == '__main__':
    main()

