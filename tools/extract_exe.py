#!/usr/bin/env python3
"""Reconstrucción del número ERNSC2-1 (Año II Nº1, Septiembre 1999).

Este número NO tiene fuente VB (.vbp/.frm/.frx); sólo se conserva el EXE
compilado (VB4 32-bit) y sus archivos acompañantes en ``ERNSC2-1/``. Los
textos de los artículos viven embebidos en el EXE como cadenas CP1252.

Estrategia de extracción (reproducible y documentada):
  1. Recorrer el EXE byte a byte y aislar "runs" de bytes imprimibles
     (TAB/LF/CR + 0x20-0xFF, incluye 0xA0-0xFF y arte ASCII) de longitud
     > MIN_LEN con al menos MIN_NL saltos de línea. Da ~17 bloques.
  2. Emparejar cada bloque con un artículo de la lista del Readme.txt
     ("Contenido de la revista") buscando una FIRMA textual del encabezado
     de cada artículo dentro del bloque.
  3. Recortar el prefijo de basura que a veces deja el record .frx delante
     del texto real (p.ej. "Â0", "´<", "Lk") usando un MARCADOR de inicio
     por artículo; el resto del arte ASCII se preserva byte a byte.
  4. Normalizar CRLF/CR -> LF (única transformación permitida por el
     contrato) y volcar cada artículo a data/ERNSC2-1/text/<slug>.txt (UTF-8).

Uso: python3 tools/extract_exe.py            (escribe los .txt y reporta)
     python3 tools/extract_exe.py --dry-run  (sólo reporta, no escribe)

El emparejamiento es determinista: mismas firmas => mismo resultado.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "ERNSC2-1" / "El Radiaktivo Newz.exe"
OUT_DIR = ROOT / "data" / "ERNSC2-1" / "text"

MIN_LEN = 250   # longitud mínima del run
MIN_NL = 3      # nº mínimo de saltos de línea

# Tabla de artículos. Orden = orden de la lista "Contenido de la revista".
#   slug      -> nombre del .txt (sin extensión)
#   signature -> subcadena que identifica el bloque del EXE (encabezado)
#   start     -> marcador de inicio del texto real; recorta el prefijo .frx
#                (None = sin recorte, se conserva el bloque completo)
#   title     -> título humano
#   author    -> autor/traductor según el Readme
ARTICLES = [
    dict(slug="editorial", title="Editorial", author="BadBit",
         signature="Se ha pasado a otra etapa en el Radiaktivo",
         start="Se ha pasado a otra etapa en el Radiaktivo"),
    dict(slug="novedades", title="Novedades", author="ERN Team",
         signature="El imperio ha ganado la guerra de los clones",
         start="El imperio ha ganado la guerra de los clones"),
    dict(slug="feedback", title="Feedback", author="Varios",
         signature="FEEDBACK",
         start="FEEDBACK"),
    dict(slug="encripcion", title="Encripción", author="BadBit",
         signature="Encripci",
         start="El Radiaktivo Newz Team presenta:"),
    dict(slug="hackweb", title="Hacking Webpages", author="kibitzer",
         signature="Hacking Webpages",
         start="Jueves 9 de septiembre"),
    dict(slug="micros", title="La verdad sobre los microprocesadores",
         author="BadBit",
         signature="La verdad sobre los microprocesadores",
         start="El Radiaktivo Newz Team presenta:"),
    dict(slug="passwords", title="Algunos passwords para su diversión",
         author="Varios",
         signature="los antivirus son un fraude",
         start="Ahora tenemos la prueba"),
    dict(slug="djhell", title="DJ-HELL Report #6", author="DJ-HELL",
         signature="Report #6",
         start=None),
    dict(slug="acidboy", title="AcidBoy", author="aCiDBoY",
         signature="Traido desde Silycon Valley",
         start="Traido desde Silycon Valley"),
    dict(slug="secretos", title="Secretos", author="acri",
         signature="Secretos por acri",
         start=None),
    dict(slug="derechos", title="Nuestros derechos constitucionales",
         author="Varios",
         signature="LA REPUBLICA: EL EQUILIBRIO DEL PODER",
         start="LA REPUBLICA: EL EQUILIBRIO DEL PODER"),
    dict(slug="miembros", title="Área de miembros de ERN", author="BadBit",
         signature="nuevos miembros viven en Mexicali",
         start=None),
    dict(slug="habit0", title="Las Aventuras de HaBit0", author="BadBit",
         signature="Las Aventuras de HaBit0",
         start="Las Aventuras de HaBit0"),
    dict(slug="banano", title="#Banano'sBar", author="Varios",
         signature="Un buffer donde intervienen los miembros",
         start="[Un buffer donde intervienen los miembros"),
    dict(slug="limbo", title="Limbo's Music", author="kibitzer",
         signature="EnTrEVISTa con PLastILinA MosH",
         start="kIBiTzER PrEsEnTA:"),
    dict(slug="perdidos", title="Perdidos en el cyberespacio", author="BadBit",
         signature="Comandancia de polic",
         start="[Escenario: Comandancia de polic"),
    dict(slug="aclaracion", title="Aclaración", author="ERN Team",
         signature="NO somos responsables de las acciones",
         start="Antes de que hagas nada"),
]


def is_print(b: int) -> bool:
    return b in (9, 10, 13) or (32 <= b <= 255)


def find_runs(data: bytes):
    """Devuelve lista de (offset, bytes) de runs imprimibles largos."""
    runs = []
    cur = bytearray()
    start = 0
    for i, b in enumerate(data):
        if is_print(b):
            if not cur:
                start = i
            cur.append(b)
        else:
            if len(cur) > MIN_LEN and (cur.count(10) + cur.count(13)) >= MIN_NL:
                runs.append((start, bytes(cur)))
            cur = bytearray()
    if len(cur) > MIN_LEN and (cur.count(10) + cur.count(13)) >= MIN_NL:
        runs.append((start, bytes(cur)))
    return runs


def decode_block(raw: bytes) -> str:
    """CP1252 -> str, normalizando CRLF/CR -> LF (única transformación)."""
    txt = raw.decode("cp1252")
    return txt.replace("\r\n", "\n").replace("\r", "\n")


def main(argv):
    dry = "--dry-run" in argv
    if not EXE.exists():
        print(f"ERROR: no existe {EXE}", file=sys.stderr)
        return 2

    data = EXE.read_bytes()
    runs = find_runs(data)
    decoded = [(off, decode_block(raw)) for off, raw in runs]
    print(f"EXE: {EXE.name} ({len(data)} bytes)")
    print(f"Runs candidatos (>{MIN_LEN} bytes, >={MIN_NL} saltos): {len(runs)}\n")

    if not dry:
        OUT_DIR.mkdir(parents=True, exist_ok=True)

    used = set()
    mapped = []
    for art in ARTICLES:
        hit = None
        for idx, (off, txt) in enumerate(decoded):
            if idx in used:
                continue
            if art["signature"] in txt:
                hit = (idx, off, txt)
                break
        if hit is None:
            print(f"  [SIN EMPAREJAR] {art['slug']:<12} firma={art['signature']!r}")
            continue
        idx, off, txt = hit
        used.add(idx)
        # recortar prefijo .frx si hay marcador
        if art["start"]:
            pos = txt.find(art["start"])
            if pos > 0:
                txt = txt[pos:]
        txt = txt.rstrip() + "\n"
        out = OUT_DIR / f"{art['slug']}.txt"
        if not dry:
            out.write_text(txt, encoding="utf-8")
        mapped.append((art, idx, off, len(txt)))
        print(f"  block {idx:<2} off={off:<7} -> text/{art['slug']}.txt "
              f"({len(txt)} chars)  [{art['title']} — {art['author']}]")

    unmatched = [i for i in range(len(decoded)) if i not in used]
    print(f"\nEmparejados: {len(mapped)}/{len(ARTICLES)} artículos")
    if unmatched:
        print(f"Bloques del EXE sin emparejar: {len(unmatched)}")
        for i in unmatched:
            off, txt = decoded[i]
            head = txt.strip().replace("\n", " ")[:70]
            print(f"  block {i} off={off}: {head!r}")
    else:
        print("Bloques del EXE sin emparejar: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
