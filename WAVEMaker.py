import argparse
import math
from pathlib import Path
import sys
from time import perf_counter


def get_args():
    parser = argparse.ArgumentParser(description='WAVE Maker')
    parser.add_argument('file', metavar='File', type=str, nargs=1, help='WAVE file to work on')
    parser.add_argument('-c', metavar='Comp', type=int, nargs='?', const=1, help='Compression format (1 is PCM and default)')

    return parser.parse_args()


def get_sin_wave_generator(freq, sample_rate, amplitude):
    period = int(sample_rate // freq) + 1
    lookup_table = [float(amplitude) * math.sin(2.0 * math.pi * float(freq) * (i / sample_rate)) for i in range(period)]
    i = 0
    while True:
        yield lookup_table[i]
        i += 1
        i %= period


def get_sin_channel(freq, sample_rate, amplitude, n_samples, bits_per_sample):
    sin_generator = get_sin_wave_generator(freq, sample_rate, amplitude)
    max_amplitude = ((1 << bits_per_sample) / 2) - 1
    channel = bytearray()

    bits_per_sample_rounded = (bits_per_sample + 7) & (-8)  # Round up to the nearest multiple of 8
    unused_bits = bits_per_sample_rounded - bits_per_sample

    for i in range(n_samples):
        channel.extend(int(max_amplitude * next(sin_generator)).to_bytes(bits_per_sample, 'little', signed=True))
        for j in range(unused_bits):
            channel.append(1)

    return channel


def get_channels(n_channels, sample_rate, bits_per_sample, n_samples, mode='sine'):
    start = perf_counter()
    if mode != 'sine':
        sys.exit('Not yet implemented')
    else:
        data = bytearray()
        channels = []
        bps_r = (bits_per_sample + 7) & (-8)  # Round up to the nearest multiple of 8
        for i in range(n_channels):
            c = bytes(get_sin_channel(2048, sample_rate, 1, n_samples, bps_r))
            channels.append([c[k:k+(bps_r//8)] for k in range(0, len(c), (bps_r//8))])

        for i in range(n_samples):
            for channel in channels:
                data.extend(channel[i])

        print(f'get_channels() took: {perf_counter() - start}')
        return data


def get_header_chunk(fmt, sample_rate, bits_per_sample, n_channels, n_samples):
    """Generates Header and Format chunks"""
    chunk_size = None
    bps_r = (bits_per_sample + 7) & (-8)  # Round up to the nearest multiple of 8

    if fmt == 1:  # PCM
        chunk_size = 36 + (n_samples * n_channels * bps_r // 8)
        header = bytes('RIFF', 'ascii')                                                                         # 0     RIFF Chunk ID
        header += chunk_size.to_bytes(length=4, byteorder='little')                                             # 4     Filesize - 8
        header += bytes('WAVE', 'ascii')                                                                        # 8     Format code (WAVE)

        header += bytes('fmt ', 'ascii')                                                                        # 12    Format Chunk ID
        header += int(16).to_bytes(length=4, byteorder='little')                                                # 16    Format Chunk Size (16 for PCM)
        header += fmt.to_bytes(length=2, byteorder='little')                                                    # 20    Format Code (1 for PCM)
        header += n_channels.to_bytes(length=2, byteorder='little')                                             # 22    Number of channels
        header += sample_rate.to_bytes(length=4, byteorder='little')                                            # 24    Sample rate
        header += (sample_rate * n_channels * bps_r // 8).to_bytes(length=4, byteorder='little')                # 28    Byte rate
        header += (n_channels * bps_r // 8).to_bytes(length=2, byteorder='little')                              # 32    Block allign: The number of bytes for one sample across all channels
        header += bps_r.to_bytes(length=2, byteorder='little')                                                  # 34    Bits per sample
        return header

    else:
        sys.exit('Non-PCM compression not yet implemented')


def get_pcm_data_chunk(sample_rate, bits_per_sample, n_channels, n_samples):
    bps_r = (bits_per_sample + 7) & (-8)  # Round up to the nearest multiple of 8
    data = bytes('data', 'ascii')
    data += (n_samples * n_channels * bps_r // 8).to_bytes(length=4, byteorder='little')
    samples = get_channels(n_channels, sample_rate, bits_per_sample, n_samples)
    start = perf_counter()
    # for sample in samples:
    #     data += sample
    data += bytes(samples)

    print(f'get_pcm_data_chunk() took: {perf_counter() - start}')
    return data


def make_file(fname, sample_rate, bits_per_sample, n_channels, duration):
    n_samples = duration * sample_rate
    fpath = Path(fname)
    with open(fpath, 'wb') as f:
        f.write(get_header_chunk(1, sample_rate, bits_per_sample, n_channels, n_samples))
        f.write(get_pcm_data_chunk(sample_rate, bits_per_sample, n_channels, n_samples))
        f.close()


def main():
    # args = vars(get_args())
    start = perf_counter()
    make_file('test.wav', 44100, 24, 2, 3)
    stop = perf_counter()
    print(f'Time taken: {stop - start}')


if __name__ == '__main__':
    main()

