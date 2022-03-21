from eventio import EventIOFile
from argparse import ArgumentParser
from eventio.simtel import HistoryMeta
from eventio.search_utils import yield_toplevel_of_type

parser = ArgumentParser()
parser.add_argument('inputfile')
parser.add_argument('--encoding', default='utf8', help='Encoding to use for decoding METAPARAMs')


def main():
    args = parser.parse_args()

    with EventIOFile(args.inputfile) as f:
        found_meta = False

        for o in f:
            # METAPARAM objects come at the toplevel after the history blocks
            # read all history meta and as soon as another objects comes, stop
            # so we don't have to read through the complete file
            if isinstance(o, HistoryMeta):
                found_meta = True
            else:
                if found_meta:
                    break
                else:
                    continue

            if o.header.id == -1:
                s = "Global METAPARAMs"
                print()
                print(s)
                print(len(s) * "-")
            else:
                s = f"METAPARAMs for telescope={o.header.id}"
                print()
                print(s)
                print(len(s) * "-")

            for k, v in o.parse().items():
                print(k.decode(args.encoding), "=", v.decode(args.encoding))



if __name__ == '__main__':
    main()

