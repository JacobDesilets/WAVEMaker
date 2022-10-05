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

        if self.fmt == 'PCM' or self.fmt == 'PCM-wavl':
            chunk += int(16).to_bytes(length=4, byteorder='little')
            chunk += int(1).to_bytes(length=2, byteorder='little')
            chunk += self.n_channels.to_bytes(length=2, byteorder='little')
            chunk += self.sample_rate.to_bytes(length=4, byteorder='little')
            byte_rate = (self.sample_rate * self.n_channels * self.bit_depth_rounded // 8)
            chunk += byte_rate.to_bytes(length=4, byteorder='little')
            block_align = (self.n_channels * self.bit_depth_rounded // 8)
            chunk += block_align.to_bytes(length=2, byteorder='little')
            # TODO: Figure out which one???
            # chunk += self.bit_depth_rounded.to_bytes(length=2, byteorder='little')
            chunk += self.bit_depth.to_bytes(length=2, byteorder='little')
        else:
            sys.exit('Non-PCM compression not yet implemented')
            # TODO: Implement

        return chunk

    def get_fact_chunk(self, n_samples_overwrite=0):
        chunk = bytes('fact', 'ascii')
        chunk += int(4).to_bytes(length=4, byteorder='little')
        if n_samples_overwrite:
            chunk += n_samples_overwrite.to_bytes(length=4, byteorder='little')
        else:
            chunk += self.n_samples.to_bytes(length=4, byteorder='little')

        return chunk

    def get_slnt_chunk(self, n_silent_samples: int):
        chunk = bytes('slnt', 'ascii')
        chunk += int(4).to_bytes(length=4, byteorder='little')
        chunk += n_silent_samples.to_bytes(length=4, byteorder='little')

        return chunk

    def get_wavl_chunk(self, n_silent_samples=20000, no_data=False) -> bytes:
        chunk = bytes('LIST', 'ascii')
        subchunks = self.get_slnt_chunk(n_silent_samples)
        if not no_data:
            subchunks += self.get_pcm_data_chunk()

        chunk_size = len(subchunks)
        chunk += chunk_size.to_bytes(length=4, byteorder='little')
        chunk += bytes('wavl', 'ascii')
        chunk += subchunks
        return chunk

    def get_cue_chunk(self, n_cues, chunk_id_overwrite='cue '):
        chunk = bytes(chunk_id_overwrite, 'ascii')
        chunk_size = 4

        for i in range(n_cues):
            cue_point = i.to_bytes(length=4, byteorder='little')        # dwName
            cue_point += i.to_bytes(length=4, byteorder='little')       # dwPosition (sample # for the cue)
            cue_point += bytes('data', 'ascii')                         # fccChunk (data or slnt, depending on where the cue occurs)
            cue_point += int(0).to_bytes(length=4, byteorder='little')  # dwChunkStart (0 if no wavl chunk present)

    def get_plst_chunk(self, n_cues):
        chunk = bytes('plst', 'ascii')
        chunk_size = n_cues * 12
        chunk += chunk_size.to_bytes(length=4, byteorder='little')

        return chunk

    def get_junk_chunk(self, hidden_text):
        chunk = bytes('JUNK', 'ascii')
        text_bytes = bytes(hidden_text, 'ascii')
        chunk_size = len(text_bytes)
        chunk += chunk_size.to_bytes(length=4, byteorder='little')
        chunk += text_bytes

        return chunk

    def get_pad_chunk(self, hidden_text):
        chunk = bytes('PAD ', 'ascii')
        text_bytes = bytes(hidden_text, 'ascii')
        chunk_size = len(text_bytes)
        chunk += chunk_size.to_bytes(length=4, byteorder='little')
        chunk += text_bytes

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
            elif self.fmt == 'PCM-wavl':
                f.write(self.get_wavl_chunk())


def get_args():
    parser = argparse.ArgumentParser(description='WAVE Maker')
    parser.add_argument('file', metavar='File', type=str, nargs=1, help='WAVE file to work on')
    parser.add_argument('-f', metavar='Format', type=str, nargs='?', const='PCM', help='Compression format (1 is PCM and default)')

    return parser.parse_args()


def main():
    start = perf_counter()
    wavemaker = Wave(bit_depth=16, n_channels=2, duration=3, fmt='PCM-wavl')
    wavemaker.white_noise()
    wavemaker.make_file('test3.wav')
    print(f'Finished in {perf_counter() - start} seconds.')


if __name__ == '__main__':
    main()
