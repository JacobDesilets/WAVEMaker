import wave
from pathlib import Path

from bitarray import bitarray


def write_steg(fname, text):
    fp = Path(fname)
    with wave.open(fname, 'rb') as wf:
        data = wf.readframes(wf.getnframes())
        text = bitarray()


def main():
    pass


if __name__ == '__main__':
    main()
