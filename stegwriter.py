import argparse
import wave
from pathlib import Path

from bitarray import bitarray


def write_steg(fname, input):
    with open(input, 'rb') as inf:
        inf_bytes = inf.read()
        text = bitarray()
        text.frombytes(inf_bytes)
        bits = text.tolist()

        with wave.open(fname, 'rb') as wf:
            params = wf.getparams()
            data = bytearray(wf.readframes(wf.getnframes()))

            for i, bit in enumerate(bits):
                data[i] = (data[i] & 254) | bit

            wf.close()

        with wave.open(fname, 'wb') as wf:
            wf.setparams(params)
            wf.writeframes(data)
            wf.close()

        inf.close()


def get_args():
    parser = argparse.ArgumentParser(description='WAVE Steganography Writer')
    parser.add_argument('WAVE file', metavar='wf', type=str, nargs=1, help='WAVE file to embed information in')
    parser.add_argument('Input file', metavar='if', type=str, nargs=1, help='Input file to embed in WAVE file')

    return parser.parse_args()


def main():
    args = vars(get_args())
    write_steg(args['WAVE file'][0], args['Input file'][0])


if __name__ == '__main__':
    main()
