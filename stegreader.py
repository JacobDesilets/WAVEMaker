import traceback
import wave
from pathlib import Path

from bitarray import bitarray
import argparse


def read_steg(fname, output):
    with open(output, 'w') as of:
        output_data = ''
        with wave.open(fname, 'rb') as wf:
            data = wf.readframes(wf.getnframes())
            text = bitarray()

            for byte in data:
                byte = byte.to_bytes(1, 'little')
                bits = bitarray()
                bits.frombytes(byte)
                text.append(bits[-1])

            text_bytes = text.tobytes()
            try:
                for byte in text_bytes:
                    byte = byte.to_bytes(1, 'little')
                    output_data += byte.decode('utf-8')
                    #print(byte.decode('utf-8'),end='')
            except UnicodeDecodeError as e:
                print('Reached end of data')
            except Exception as e:
                print(e)

            wf.close()

        of.write(output_data)
        of.close()


def get_args():
    parser = argparse.ArgumentParser(description='WAVE Steganography Writer')
    parser.add_argument('WAVE file', metavar='wf', type=str, nargs=1, help='WAVE file to embed information in')
    parser.add_argument('Output file', metavar='of', type=str, nargs=1, help='Input file to embed in WAVE file')

    return parser.parse_args()


def main():
    args = vars(get_args())
    read_steg(args['WAVE file'][0], args['Output file'][0])


if __name__ == '__main__':
    main()