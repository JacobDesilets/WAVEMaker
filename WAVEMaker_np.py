import argparse
import math
from pathlib import Path
import sys
from time import perf_counter
import numpy as np
from bitarray import bitarray


class Wave:
    def __init__(self, sample_rate=44100, bit_depth=16, n_channels=2, duration=3, fmt='PCM', junk='no'):
        self.sample_rate = sample_rate                      # Sample rate in Hz
        self.bit_depth = bit_depth                          # Bits per sample
        self.n_channels = n_channels                        # Channel count
        self.duration = duration                            # Length of audio in seconds
        self.n_samples = self.duration * self.sample_rate
        self.fmt = fmt                                      # Compression format (String)

        self.bit_depth_rounded = (self.bit_depth + 7) & (-8)  # Bits per sample must be multiple of 8
        self.np_dt = f'<i{int(self.bit_depth_rounded / 8)}'
        self.data = np.zeros((self.n_samples, self.n_channels), dtype=self.np_dt)

        self.junk = junk

    def white_noise(self):
        max_amplitude = ((1 << self.bit_depth) / 2) - 1
        r = (np.random.uniform(-1, 1, (self.n_samples, self.n_channels)) * max_amplitude).astype(self.np_dt)
        self.data = r

    def get_header_chunk(self, options):
        chunk = bytes(options['header_chunkid'], 'ascii')
        options_size = int(options['header_size'])
        if options_size == -1:
            chunk_size = 36 + (self.n_samples * self.n_channels * self.bit_depth_rounded // 8)
        else:
            chunk_size = options_size
        chunk += chunk_size.to_bytes(length=4, byteorder='little')
        chunk += bytes(options['header_formtype'], 'ascii')

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

    def get_slnt_chunk(self, options):
        chunk = bytes(options['slnt-chunkid'], 'ascii')
        chunk += int(4).to_bytes(length=4, byteorder='little')
        chunk += int(options['slnt-nsamples']).to_bytes(length=4, byteorder='little')

        return chunk

    def get_wavl_chunk(self, options, n_silent_samples=20000) -> bytes:
        chunk = bytes(options['wavl_chunkid'], 'ascii')
        subchunks = self.get_slnt_chunk(n_silent_samples)
        if options['wavl_hasdata'] == 'yes':
            subchunks += self.get_pcm_data_chunk()

        if options['wavl_slntalt'] == 'yes':
            subchunks += self.get_slnt_chunk(n_silent_samples)

        chunk_size = len(subchunks)
        chunk += chunk_size.to_bytes(length=4, byteorder='little')
        chunk += bytes(options['wavl_formtype'], 'ascii')
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

    def get_junk_chunk(self, options):
        chunk = bytes(options['junk-chunkid'], 'ascii')
        if options['junk-hiddentext'] != '':
            text_bytes = bytes(options['junk-hiddentext'], 'ascii')
        else:
            text_bytes = b'0xff0xff0xff0xff0xff0xff0xff0xff'
        if options['junk-size'] != -1:
            chunk_size = len(text_bytes)
        else:
            chunk_size = options['junk-size']
        chunk += chunk_size.to_bytes(length=4, byteorder='little')
        chunk += text_bytes

        return chunk

    def get_pad_chunk(self, options):
        chunk = bytes(options['pad-chunkid'], 'ascii')
        if options['pad-hiddentext'] != '':
            text_bytes = bytes(options['pad-hiddentext'], 'ascii')
        else:
            text_bytes = b'0xff0xff0xff0xff0xff0xff0xff0xff'
        if options['pad-size'] != -1:
            chunk_size = len(text_bytes)
        else:
            chunk_size = options['pad-size']
        chunk += chunk_size.to_bytes(length=4, byteorder='little')
        chunk += text_bytes

        return chunk

    def get_pcm_data_chunk(self, steg=''):
        chunk = bytes('data', 'ascii')
        chunk_size = int(self.n_samples * self.n_channels * self.bit_depth_rounded / 8)
        chunk += chunk_size.to_bytes(length=4, byteorder='little')
        interleaved_bytes = bytearray(np.column_stack(self.data.tolist()).astype(self.np_dt).tobytes())
        if steg:
            text = bitarray()
            text.frombytes(steg.encode('ascii'))
            bits = text.tolist()

            for i, bit in enumerate(bits):
                interleaved_bytes[i] = (interleaved_bytes[i] & 254) | bit

        chunk += bytes(interleaved_bytes)

        return chunk

    def make_file(self, fname, options):
        fp = Path(fname)
        with open(fp, 'wb') as f:
            f.write(self.get_header_chunk(options))
            f.write(self.get_fmt_chunk())
            if self.fmt == 'PCM':
                f.write(self.get_pcm_data_chunk())
            elif self.fmt == 'PCM-wavl':
                f.write(self.get_wavl_chunk(options))

            if self.junk == 'junk':
                f.write(self.get_junk_chunk(options))
            elif self.junk == 'pad':
                f.write(self.get_pad_chunk(options))


def main():
    options = {}

    hline = '=' * 30
    print(f'==== WaveMaker {hline}')
    print('Options: (Leave blank for defaults)')
    sample_rate = int(input('Sample Rate in hz (44100)\t>> ') or 44100)
    bit_depth = int(input('Bit Depth (16)\t\t\t>> ') or 16)
    n_channels = int(input('Number of Channels (2)\t\t>> ') or 2)
    duration = int(input('Length in Seconds (3)\t\t>> ') or 3)
    fmt = (input('Compression Format (PCM)\t>> ') or 'PCM')
    fname = (input('Output File Name (audio.wav)\t>> ') or 'audio.wav')
    junk = (input('Include junk or pad chunk (no)\t>> ') or 'no')
    print(f'==== Chunk Modifications {hline}')
    done = False
    while not done:
        print('0: Done\n1: Modify header chunk\n2: Modify format chunk\n3: Modify Data Chunk')
        if fmt == 'PCM-wavl':
            print('4: Modify list chunk\n5: Modify silent chunk')
        if junk == 'junk':
            print('6: Modify junk chunk')
        elif junk == 'pad':
            print('7: Modify pad chunk')

        print()

        option = int(input('>>> '))
        match option:
            case 0:
                options['header_chunkid'] = 'RIFF'
                options['header_size'] = '-1'
                options['header_formtype'] = 'WAVE'

                options['wavl_chunkid'] = 'LIST'
                options['wavl_formtype'] = 'wavl'
                options['wavl_hasdata'] = 'yes'
                options['wavl_slntalt'] = 'no'

                options['junk-chunkid'] = 'JUNK'
                options['junk-size'] = '-1'
                options['junk-hiddentext'] = ''

                options['pad-chunkid'] = 'JUNK'
                options['pad-size'] = '-1'
                options['pad-hiddentext'] = ''

                options['slnt-chunkid'] = 'slnt'
                options['slnt-nsamples'] = '4'

                break
            case 1:
                options['header_chunkid'] = (input('Chunk ID (RIFF)\t\t>>> ') or 'RIFF')
                options['header_size'] = (input('Size (correct value)\t>>> ') or '-1')
                options['header_formtype'] = (input('Form Type (WAVE)\t>>> ') or 'WAVE')
            case 4:
                options['wavl_chunkid'] = (input('Chunk ID (LIST)\t\t>>> ') or 'LIST')
                options['wavl_formtype'] = (input('Form type (wavl)\t\t>>> ') or 'wavl')
                options['wavl_hasdata'] = (input('Include data [yes or no] (yes)\t\t>>> ') or 'yes')
                options['wavl_slntalt'] = (input('Include contiguous slnt chunks [yes or no] (no)\t\t>>> ') or 'no')
            case 5:
                options['slnt-chunkid'] = (input('Chunk ID (slnt)\t\t>>> ') or 'slnt')
                options['slnt-nsamples'] = (input('Number of silent samples (4)\t\t>>> ') or '4')
            case 6:
                options['junk-chunkid'] = (input('Chunk ID (JUNK)\t\t>>> ') or 'JUNK')
                options['junk-size'] = (input('Size (correct value)\t\t>>> ') or '-1')
                options['junk-hiddentext'] = (input('Hidden text (none)\t\t>>> ') or '')
            case 7:
                options['pad-chunkid'] = (input('Chunk ID (PAD )\t\t>>> ') or 'PAD ')
                options['pad-size'] = (input('Size (correct value)\t\t>>> ') or '-1')
                options['pad-hiddentext'] = (input('Hidden text (none)\t\t>>> ') or '')

    start = perf_counter()
    wavemaker = Wave(sample_rate, bit_depth, n_channels, duration, fmt)
    wavemaker.white_noise()
    wavemaker.make_file(fname, options)
    print(f'Made {fname} in {perf_counter() - start} seconds.')


if __name__ == '__main__':
    main()
