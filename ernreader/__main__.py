"""Entry point: ``python -m ernreader [--data DIR]`` opens the launcher."""

from __future__ import annotations

import argparse
import os
import sys

from .launcher import Launcher


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ernreader",
        description="Lector Win95 de El Radiaktivo Newz.")
    parser.add_argument("--data", default="data",
                        help="Directorio con los números extraídos "
                             "(por defecto: data/)")
    args = parser.parse_args(argv)

    data_dir = os.path.abspath(args.data)
    if not os.path.isdir(data_dir):
        print(f"[ernreader] aviso: no existe el directorio de datos "
              f"{data_dir!r}; se mostrará el lanzador vacío.", file=sys.stderr)

    app = Launcher(data_dir)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
