from eventio import EventIOFile
from argparse import ArgumentParser
from eventio.simtel import History
from datetime import datetime

parser = ArgumentParser()
parser.add_argument('inputfile')


def main():
    args = parser.parse_args()

    with EventIOFile(args.inputfile) as f:
        o = next(f)
        while isinstance(o, History):
            for subo in o:
                t, line = subo.parse()
                t = datetime.fromtimestamp(t)
                print(f'{t:%Y-%m-%dT%H:%M:%S}', line.decode('utf-8').strip())
            o = next(f)


if __name__ == '__main__':
    main()
