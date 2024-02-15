import sys

import json
from eventio import EventIOFile
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from eventio.simtel import HistoryMeta
from difflib import unified_diff

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('inputfile')
parser.add_argument('--encoding', default='utf8', help='Encoding to use for decoding METAPARAMs')

group = parser.add_mutually_exclusive_group()
group.add_argument('--tel-diff', nargs=2, type=int)
group.add_argument("--json", action="store_true", help="output as json")


def print_metaparams():
    args = parser.parse_args()

    global_meta, telescope_meta = read_meta(args.inputfile, args.encoding)

    if args.tel_diff is not None:
        tel_a, tel_b = args.tel_diff

        meta_a = telescope_meta[tel_a]
        meta_b = telescope_meta[tel_b]

        diff = unified_diff(format_meta(meta_a).splitlines(), format_meta(meta_b).splitlines())
        for line in diff:
            print(line)
        sys.exit(0)

    if args.json:
        meta = {"global": global_meta, "telescopes": telescope_meta}
        print(json.dumps(meta, indent=2))
        sys.exit(0)

    if global_meta is not None:
        print_meta(global_meta)

    for tel_id, meta in telescope_meta.items():
        print()
        print_meta(meta, tel_id=tel_id)


def read_meta(path, encoding):
    global_meta = None
    telescope_meta = {}

    with EventIOFile(path) as f:
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
                global_meta = decode(o.parse(), encoding)
            else:
                telescope_meta[o.header.id] = decode(o.parse(), encoding)

    return global_meta, telescope_meta


def decode(meta, encoding):
    return {
        k.decode(encoding): v.decode(encoding)
        for k, v in meta.items()
    }


def format_meta(meta):
    return "\n".join(f"{k} = {v}" for k, v in meta.items())


def print_meta(meta, tel_id=None):
    if tel_id is None:
        title = "Global METAPARAMs"
    else:
        title = f"METAPARAMs for telescope={tel_id}"

    print(title)
    print(len(title) * "-")
    print(format_meta(meta))


def main():
    try:
        print_metaparams()
    except BrokenPipeError:
        pass


if __name__ == '__main__':
    main()

