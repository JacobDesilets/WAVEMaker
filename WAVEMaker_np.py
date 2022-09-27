import argparse
import math
from pathlib import Path
import sys
from time import perf_counter
import numpy as np


class Wave:
    def __init__(self, sample_rate=44100, bit_depth=16, n_channels=2, duration=3, fmt='PCM'):
        self.sample_rate = sample_rate                      # Sample rate in Hz
        self.bit_depth = bit_depth                          # Bits per sample
        self.n_channels = n_channels                        # Channel count
        self.duration = duration                            # Length of audio in seconds
        self.n_samples = self.duration * self.sample_rate
        self.fmt = fmt                                      # Compression format (String)

        self.bit_depth_rounded = (self.bit_depth + 7) & (-8)  # Bits per sample must be multiple of 8
        self.np_dt = f'<i{int(self.bit_depth_rounded / 8)}'
        self.data = np.zeros((self.n_samples, self.n_channels), dtype=self.np_dt)

    def white_noise(self):
        max_amplitude = ((1 << self.bit_depth) / 2) - 1
        r = (np.random.uniform(-1, 1, (self.n_samples, self.n_channels)) * max_amplitude).astype(self.np_dt)
        self.data = r

    def get_header_chunk(self):
        chunk = bytes('RIFF', 'ascii')
        chunk_size = 36 + (self.n_samples * self.n_channels * self.bit_depth_rounded // 8)
        chunk += chunk_size.to_bytes(length=4, byteorder='little')
        chunk += bytes('WAVE', 'ascii')

        return chunk

    def get_fmt_chunk(self):
        chunk = bytes('fmt ', 'ascii')

        if self.fmt == 'PCM':
            chunk += int(16).to_bytes(length=4, byteorder='little')
            chunk += int(1).to_bytes(length=2, byteorder='little')
            chunk += self.n_channels.to_bytes(length=2, byteorder='little')
            chunk += self.sample_rate.to_bytes(length=4, byteorder='little')
            byte_rate = (self.sample_rate * self.n_channels * self.bit_depth_rounded // 8)
            chunk += byte_rate.to_bytes(length=4, byteorder='little')
            block_align = (self.n_channels * self.bit_depth_rounded // 8)
            chunk += block_align.to_bytes(length=2, byteorder='little')
            # chunk += self.bit_depth_rounded.to_bytes(length=2, byteorder='little')
            chunk += self.bit_depth.to_bytes(length=2, byteorder='little')
        else:
            sys.exit('Non-PCM compression not yet implemented')
            # TODO: Implement

        return chunk

    def get_pcm_data_chunk(self):
        chunk = bytes('data', 'ascii')
        chunk_size = int(self.n_samples * self.n_channels * self.bit_depth_rounded / 8)
        chunk += chunk_size.to_bytes(length=4, byteorder='little')
        interleaved_bytes = np.column_stack(self.data.tolist()).astype(self.np_dt).tobytes()
        chunk += interleaved_bytes

        return chunk

    def make_file(self, fname):
        fp = Path(fname)
        with open(fp, 'wb') as f:
            f.write(self.get_header_chunk())
            f.write(self.get_fmt_chunk())
            if self.fmt == 'PCM':
                f.write(self.get_pcm_data_chunk())


def get_args():
    parser = argparse.ArgumentParser(description='WAVE Maker')
    parser.add_argument('file', metavar='File', type=str, nargs=1, help='WAVE file to work on')
    parser.add_argument('-c', metavar='Comp', type=int, nargs='?', const=1, help='Compression format (1 is PCM and default)')

    return parser.parse_args()


def main():
    start = perf_counter()
    wavemaker = Wave(bit_depth=16, n_channels=2, duration=3)
    wavemaker.white_noise()
    wavemaker.make_file('test2.wav')
    print(f'Finished in {perf_counter() - start} seconds.')


if __name__ == '__main__':
    main()
