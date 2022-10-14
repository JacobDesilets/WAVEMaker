import wave
from pathlib import Path

from bitarray import bitarray


def read_steg(fname):
    fp = Path(fname)
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
                print(byte.decode('ascii'),end='')
        except Exception as e:
            print(f'\n{e}')


def main():
    read_steg('steg.wav')


if __name__ == '__main__':
    main()