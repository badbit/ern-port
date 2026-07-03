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
    parser.add_argument("--scale", default="auto",
                        help="Factor de escalado de la interfaz (p. ej. 2 "
                             "para pantallas HiDPI) o 'auto' para detectarlo "
                             "del display (por defecto: auto)")
    parser.add_argument("--no-restore", action="store_true",
                        help="No ofrecer restaurar la última sesión de "
                             "lectura")
    args = parser.parse_args(argv)

    data_dir = os.path.abspath(args.data)
    if not os.path.isdir(data_dir):
        print(f"[ernreader] aviso: no existe el directorio de datos "
              f"{data_dir!r}; se mostrará el lanzador vacío.", file=sys.stderr)

    app = Launcher(data_dir, scale=args.scale, restore=not args.no_restore)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
