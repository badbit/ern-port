#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_vb.py — Fase 1 del port de "El Radiaktivo Newz".

Parsea los proyectos Visual Basic 4/5/6 (.vbp/.frm/.frx) de cada numero y
genera el contrato de datos descrito en docs/PORTING.md:

    data/<ISSUE>/manifest.json
    data/<ISSUE>/assets/*.png
    data/<ISSUE>/text/*.txt

Solo usa stdlib + Pillow. Los fuentes en ERNSC*/ son de SOLO LECTURA.

Uso:
    python3 tools/extract_vb.py --all
    python3 tools/extract_vb.py --issue ERNSC1-1
"""

from __future__ import annotations

import argparse
import codecs
import io
import json
import os
import re
import shutil
import struct
import sys
import unicodedata


def _cp1252_fallback(err):
    """Preserva byte-a-byte los 5 bytes indefinidos de CP1252 (0x81,0x8D,0x8F,
    0x90,0x9D) mapeandolos a su codepoint latin-1 en vez de perder datos."""
    raw = err.object[err.start:err.end]
    return ("".join(chr(b) for b in raw), err.end)


codecs.register_error("cp1252fallback", _cp1252_fallback)


def dsrc(b):
    """Decodifica bytes de fuente VB (CP1252) sin perder bytes indefinidos."""
    return b.decode(SRC_ENCODING, "cp1252fallback")

try:
    from PIL import Image
except Exception as exc:  # pragma: no cover
    sys.stderr.write("ERROR: se requiere Pillow (pip install Pillow): %s\n" % exc)
    raise

# ---------------------------------------------------------------------------
# Rutas / constantes
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ROOT = os.path.join(REPO_ROOT, "data")

ISSUES = [
    "ERNSC1-1", "ERNSC1-2", "ERNSC1-3", "ERNSC1-4", "ERNSC1-5",
    "ERNSC1-6", "ERNSC2-2", "ERNSC2-3", "ERNSC2-4", "ERNSC2-5",
]

SRC_ENCODING = "cp1252"

# Paleta clasica Win95 para colores de sistema &H8000000X&.
# Los indices que el contrato fija explicitamente estan marcados con (C).
SYS_COLORS = {
    0x00: "#C0C0C0",  # ScrollBar
    0x01: "#008080",  # Desktop (C)
    0x02: "#000080",  # ActiveTitle (C)
    0x03: "#808080",  # InactiveTitle
    0x04: "#C0C0C0",  # Menu
    0x05: "#FFFFFF",  # Window (C)
    0x06: "#000000",  # WindowFrame
    0x07: "#000000",  # MenuText
    0x08: "#000000",  # WindowText (C)
    0x09: "#FFFFFF",  # CaptionText
    0x0A: "#808080",  # InactiveTitle/ActiveBorder (C)
    0x0B: "#C0C0C0",  # InactiveBorder
    0x0C: "#C0C0C0",  # AppWorkspace
    0x0D: "#000080",  # Highlight (C)
    0x0E: "#FFFFFF",  # HighlightText (C)
    0x0F: "#C0C0C0",  # ButtonFace (C)
    0x10: "#808080",  # ButtonShadow (C)
    0x11: "#000000",  # GrayText
    0x12: "#000000",  # ButtonText (C)
    0x13: "#FFFFFF",  # InactiveCaptionText
    0x14: "#FFFFFF",  # ButtonHighlight (C)
    0x15: "#000000",  # 3DDkShadow
    0x16: "#C0C0C0",  # 3DLight
    0x17: "#000000",  # InfoText
    0x18: "#FFFFE1",  # InfoBackground
}

# Propiedades booleanas conocidas (VB: -1 = True, 0 = False).
BOOL_PROPS = {
    "maxbutton", "minbutton", "autosize", "wordwrap", "locked", "multiline",
    "visible", "enabled", "stretch", "default", "cancel", "tabstop",
    "windowlist", "clipcontrols", "autoredraw", "controlbox", "keypreview",
    "showintaskbar", "usemaskcolor", "checked", "negotiateposition",
    "whatsthisbutton", "whatsthishelp",
}

COLOR_PROPS = {
    "forecolor", "backcolor", "bordercolor", "fillcolor", "maskcolor",
}

# Propiedades que pueden contener texto largo (inline o via .frx).
TEXT_PROPS = {"caption", "text"}

# Propiedades que referencian imagenes en .frx / disco.
IMAGE_PROPS = {"icon", "picture", "mouseicon", "image", "dragicon"}

INLINE_TEXT_LIMIT = 200  # chars: por encima de esto va a text/*.txt


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def twips_to_px(twips):
    return int(round(twips / 15.0))


def norm_name(name):
    """Normaliza un nombre de archivo para resolucion tolerante."""
    return unicodedata.normalize("NFC", name).casefold()


def strip_accents(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


class Dir:
    """Directorio de un numero con resolucion tolerante de nombres."""

    def __init__(self, path):
        self.path = path
        self._by_norm = {}
        self._by_stripped = {}
        for name in os.listdir(path):
            self._by_norm[norm_name(name)] = name
            self._by_stripped.setdefault(strip_accents(name).casefold(), name)

    def resolve(self, referenced):
        """Devuelve el nombre real en disco para un nombre referenciado, o None."""
        base = os.path.basename(referenced.replace("\\", "/"))
        key = norm_name(base)
        if key in self._by_norm:
            return self._by_norm[key]
        skey = strip_accents(base).casefold()
        if skey in self._by_stripped:
            return self._by_stripped[skey]
        return None

    def read_bytes(self, referenced):
        real = self.resolve(referenced)
        if real is None:
            return None
        with open(os.path.join(self.path, real), "rb") as fh:
            return fh.read()


def parse_color(raw_value):
    """(&H00BBGGRR& | &H8000000X& | decimal) -> ('#RRGGBB' | None, original_str)."""
    original = raw_value
    v = raw_value.strip()
    m = re.match(r"&H([0-9A-Fa-f]+)&?", v)
    if m:
        val = int(m.group(1), 16)
    else:
        try:
            val = int(v)
        except ValueError:
            return None, original
        val &= 0xFFFFFFFF
    if (val & 0x80000000) == 0x80000000:
        idx = val & 0xFF
        hexc = SYS_COLORS.get(idx)
        if hexc is None:
            hexc = "#000000"
        return hexc, original
    rr = val & 0xFF
    gg = (val >> 8) & 0xFF
    bb = (val >> 16) & 0xFF
    return "#%02X%02X%02X" % (rr, gg, bb), original


def parse_bool(raw_value):
    tok = raw_value.strip().split()[0] if raw_value.strip() else "0"
    try:
        return int(tok) != 0
    except ValueError:
        return None


def parse_number(raw_value):
    tok = raw_value.strip()
    # quita comentario ' ...
    tok = re.split(r"\s+'", tok, 1)[0].strip()
    tok = tok.split()[0] if tok.split() else tok
    try:
        if "." in tok or "E" in tok or "e" in tok:
            f = float(tok)
            return int(f) if f.is_integer() else f
        return int(tok)
    except ValueError:
        return None


def clean_scalar(raw_value):
    """Limpia el comentario ' de un valor escalar crudo."""
    return re.split(r"\s+'", raw_value.strip(), 1)[0].strip()


# ---------------------------------------------------------------------------
# FRX
# ---------------------------------------------------------------------------

def _u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def _u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def _plausible_text(payload):
    if not payload:
        return True
    good = sum(1 for x in payload if x in (9, 10, 13) or 32 <= x <= 255 and x != 127)
    return good / len(payload) > 0.90


def frx_read_text(data, off, end=None):
    """Lee un registro de texto FRX. Devuelve bytes (cp1252) o None.

    Tres formatos observados empiricamente (VB4 y VB5/6):
      1. Marcador 0xFF + longitud LE de 2 bytes, payload en off+3.
      2. Longitud LE de 4 bytes, payload en off+4.
      3. SIN prefijo de longitud: el texto ocupa todo el record.

    `end` es el limite del record (offset del siguiente record en el mismo
    .frx, o el tamano del archivo). Se prioriza el candidato cuya cabecera +
    longitud caiga EXACTAMENTE en `end` (deterministico); si ninguno encaja,
    se prueba por plausibilidad y finalmente se toma el record entero (formato
    sin prefijo).
    """
    if off < 0 or off >= len(data):
        return None
    if end is None or end > len(data) or end <= off:
        end = len(data)
    span = end - off

    # (header_len, declared_length)
    cands = []
    if data[off] == 0xFF and span >= 3:
        cands.append((3, _u16(data, off + 1)))
    if span >= 4:
        cands.append((4, _u32(data, off)))
    if span >= 2:
        cands.append((2, _u16(data, off)))

    # 1) coincidencia exacta con el limite del record
    for hl, length in cands:
        if length == span - hl:
            return data[off + hl:off + hl + length]
    # 2) cabe y es texto plausible
    for hl, length in cands:
        if length == 0:
            return b""
        start = off + hl
        if 0 <= length <= end - start:
            payload = data[start:start + length]
            if _plausible_text(payload):
                return payload
    # 3) sin prefijo: el record entero es el texto
    payload = data[off:end]
    if _plausible_text(payload):
        return payload
    return None


def frx_read_image(data, off):
    """Lee un registro de imagen FRX (cabecera 'lt' de 12 bytes).

    Devuelve (payload_bytes, kind) o (None, reason).
      kind in {'BMP','ICO','CUR','GIF','JPEG','WMF','EMF','UNKNOWN'}
    Un record de tamano 0 -> (None, 'empty').
    """
    if off < 0 or off + 12 > len(data):
        return None, "oob"
    magic = data[off + 4:off + 6]
    if magic == b"lt":
        img_size = _u32(data, off + 8)
        payload = data[off + 12:off + 12 + img_size]
    else:
        # Fallback: buscar firma conocida en los primeros ~24 bytes.
        payload = data[off:off + 200000]
        img_size = len(payload)
    if img_size == 0 or not payload:
        return None, "empty"
    kind = _sniff_image(payload)
    if kind is None:
        # buscar firma dentro de los primeros 24 bytes
        for shift in range(0, min(24, len(payload))):
            k = _sniff_image(payload[shift:])
            if k:
                return payload[shift:], k
        return payload, "UNKNOWN"
    return payload, kind


def _sniff_image(b):
    if b[:2] == b"BM":
        return "BMP"
    if b[:4] == b"\x00\x00\x01\x00":
        return "ICO"
    if b[:4] == b"\x00\x00\x02\x00":
        return "CUR"
    if b[:3] == b"GIF":
        return "GIF"
    if b[:2] == b"\xff\xd8":
        return "JPEG"
    if b[:4] == b"\xd7\xcd\xc6\x9a":
        return "WMF"          # placeable metafile
    if b[:4] == b"\x01\x00\x09\x00":
        return "WMF"          # standard metafile
    if b[:4] == b"\x01\x00\x00\x00" and b"\x20EMF" in b[:64]:
        return "EMF"
    return None


def image_payload_to_png(payload, kind, out_path):
    """Convierte un payload de imagen a PNG. Devuelve (True, info) o (False, reason)."""
    if kind in ("WMF", "EMF", "UNKNOWN"):
        return False, kind  # Pillow no rasteriza metafiles en Linux
    try:
        im = Image.open(io.BytesIO(payload))
        if kind in ("ICO", "CUR") and getattr(im, "ico", None) is not None:
            # elegir el frame de mayor tamano
            try:
                sizes = list(im.ico.sizes())
                if sizes:
                    biggest = max(sizes, key=lambda s: s[0] * s[1])
                    im = im.ico.getimage(biggest)
            except Exception:
                im.load()
        else:
            im.load()
        # preservar transparencia; normalizar a RGBA si hay alfa/transparencia
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            im = im.convert("RGBA")
        elif im.mode == "P":
            im = im.convert("RGB")
        im.save(out_path, "PNG")
        return True, {"w": im.size[0], "h": im.size[1], "src": kind}
    except Exception as exc:
        return False, "%s:%s" % (kind, exc)


# ---------------------------------------------------------------------------
# Parser del .frm  (arbol generico de bloques Begin/End)
# ---------------------------------------------------------------------------

BEGIN_RE = re.compile(r"^\s*Begin\s+([A-Za-z0-9_.]+)\s+([A-Za-z0-9_]+)")
BEGINPROP_RE = re.compile(r"^\s*BeginProperty\s+([A-Za-z0-9_]+)")
PROP_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*)$")
ATTR_RE = re.compile(r"^\s*Attribute\s+")


class Node:
    __slots__ = ("libclass", "vbtype", "name", "props", "children", "propblocks")

    def __init__(self, libclass, name):
        self.libclass = libclass                       # e.g. 'VB.CommandButton'
        self.vbtype = libclass.split(".")[-1]          # e.g. 'CommandButton'
        self.name = name
        self.props = {}          # propname -> raw value string
        self.children = []       # list[Node]
        self.propblocks = {}     # BeginProperty name -> {inner props}


def parse_frm(text):
    """Devuelve (root_node, version_str, code_str)."""
    lines = text.split("\n")
    # normaliza CR sueltos
    lines = [ln.rstrip("\r") for ln in lines]

    version = None
    if lines and lines[0].startswith("VERSION"):
        version = lines[0].split()[1] if len(lines[0].split()) > 1 else None

    root = None
    stack = []            # pila de Node (contenedores)
    i = 0
    n = len(lines)
    code_start = None

    while i < n:
        ln = lines[i]
        bp = BEGINPROP_RE.match(ln)
        if bp:
            # bloque BeginProperty ... EndProperty
            blockname = bp.group(1)
            inner = {}
            i += 1
            while i < n and not re.match(r"^\s*EndProperty\b", lines[i]):
                pm = PROP_RE.match(lines[i])
                if pm:
                    inner[pm.group(1)] = pm.group(2)
                i += 1
            if stack:
                stack[-1].propblocks[blockname] = inner
            i += 1
            continue

        bm = BEGIN_RE.match(ln)
        if bm:
            node = Node(bm.group(1), bm.group(2))
            if root is None:
                root = node
            elif stack:
                stack[-1].children.append(node)
            stack.append(node)
            i += 1
            continue

        if re.match(r"^\s*End\s*$", ln):
            if stack:
                stack.pop()
                if not stack:
                    # cerramos el form: el resto es Attribute + codigo
                    code_start = i + 1
                    break
            i += 1
            continue

        if stack:
            pm = PROP_RE.match(ln)
            if pm and not ln.lstrip().startswith("'"):
                stack[-1].props[pm.group(1)] = pm.group(2)
        i += 1

    # Codigo: todo lo que sigue a la ultima linea 'Attribute ...'
    code = ""
    if code_start is not None:
        tail = lines[code_start:]
        last_attr = -1
        for idx, ln in enumerate(tail):
            if ATTR_RE.match(ln):
                last_attr = idx
        code_lines = tail[last_attr + 1:]
        code = "\n".join(code_lines)
        # recorta lineas en blanco iniciales
        code = code.lstrip("\n")

    return root, version, code


def get_vb_name(root, text):
    m = re.search(r'^Attribute VB_Name = "([^"]*)"', text, re.M)
    if m:
        return m.group(1)
    return root.name if root else None


# ---------------------------------------------------------------------------
# Parseo de valores de propiedad
# ---------------------------------------------------------------------------

def parse_string_value(raw):
    """Parsea un valor de string entre comillas VB (con "" escapado)."""
    raw = raw.strip()
    if not raw.startswith('"'):
        return None
    out = []
    i = 1
    while i < len(raw):
        c = raw[i]
        if c == '"':
            if i + 1 < len(raw) and raw[i + 1] == '"':
                out.append('"')
                i += 2
                continue
            break
        out.append(c)
        i += 1
    return "".join(out)


FRX_REF_RE = re.compile(r'^\$?"([^"]+\.frx)"\s*:\s*([0-9A-Fa-f]+)\s*$', re.I)


def parse_frx_ref(raw):
    m = FRX_REF_RE.match(raw.strip())
    if m:
        return m.group(1), int(m.group(2), 16)
    return None


# ---------------------------------------------------------------------------
# Construccion del manifest
# ---------------------------------------------------------------------------

class IssueExtractor:
    def __init__(self, issue):
        self.issue = issue
        self.src = Dir(os.path.join(REPO_ROOT, issue))
        self.out = os.path.join(DATA_ROOT, issue)
        self.assets = os.path.join(self.out, "assets")
        self.textdir = os.path.join(self.out, "text")
        self.stats = {
            "forms": 0, "controls": 0, "menus": 0, "texts": 0, "images": 0,
            "frx_refs": 0, "frx_unresolved": 0, "metafiles_skipped": 0,
            "missing_forms": [], "anomalies": [],
        }
        # frx_realname (lower) -> lista ordenada de offsets referenciados,
        # para calcular el limite de cada record.
        self._frx_offsets = {}

    def _frx_end(self, frx_ref, off, data_len):
        """Limite del record: siguiente offset referenciado, o EOF."""
        real = self.src.resolve(frx_ref)
        offs = self._frx_offsets.get((real or frx_ref).lower(), [])
        for o in offs:
            if o > off:
                return min(o, data_len)
        return data_len

    def _scan_frx_offsets(self, frm_text):
        for m in re.finditer(r'\$?"([^"]+\.frx)"\s*:\s*([0-9A-Fa-f]+)', frm_text):
            real = self.src.resolve(m.group(1))
            key = (real or m.group(1)).lower()
            self._frx_offsets.setdefault(key, set()).add(int(m.group(2), 16))

    # -- helpers de salida ---------------------------------------------------
    def _asset_path(self, basename):
        return os.path.join(self.assets, basename)

    def _rel_asset(self, basename):
        return "assets/" + basename

    def _rel_text(self, basename):
        return "text/" + basename

    def _write_text_file(self, basename, payload_bytes):
        # preserva bytes salvo CRLF/CR -> LF
        s = dsrc(payload_bytes)
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        path = os.path.join(self.textdir, basename)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(s)
        self.stats["texts"] += 1
        return self._rel_text(basename)

    def _extract_image(self, frx_name, offset, asset_basename, prop_desc):
        """Resuelve un ref FRX de imagen -> PNG. Devuelve ruta relativa o None."""
        self.stats["frx_refs"] += 1
        data = self.src.read_bytes(frx_name)
        if data is None:
            self.stats["frx_unresolved"] += 1
            self.stats["anomalies"].append(
                "FRX no encontrado: %s (%s)" % (frx_name, prop_desc))
            return None
        payload, kind = frx_read_image(data, offset)
        if payload is None:
            if kind != "empty":
                self.stats["anomalies"].append(
                    "%s: record imagen ilegible (%s) @%s:%04X"
                    % (prop_desc, kind, frx_name, offset))
            return None
        out_path = self._asset_path(asset_basename)
        ok, info = image_payload_to_png(payload, kind, out_path)
        if ok:
            self.stats["images"] += 1
            return self._rel_asset(asset_basename)
        # metafile / no rasterizable
        if kind in ("WMF", "EMF"):
            self.stats["metafiles_skipped"] += 1
            self.stats["anomalies"].append(
                "%s: metafile %s no rasterizable (Pillow/Linux) @%s:%04X -> null"
                % (prop_desc, kind, frx_name, offset))
        else:
            self.stats["anomalies"].append(
                "%s: fallo al convertir (%s) @%s:%04X" % (prop_desc, info, frx_name, offset))
        return None

    def _extract_text_ref(self, frx_name, offset, text_basename, desc):
        self.stats["frx_refs"] += 1
        data = self.src.read_bytes(frx_name)
        if data is None:
            self.stats["frx_unresolved"] += 1
            self.stats["anomalies"].append(
                "FRX no encontrado: %s (%s)" % (frx_name, desc))
            return None
        end = self._frx_end(frx_name, offset, len(data))
        payload = frx_read_text(data, offset, end)
        if payload is None:
            self.stats["frx_unresolved"] += 1
            self.stats["anomalies"].append(
                "%s: texto FRX ilegible @%s:%04X" % (desc, frx_name, offset))
            return None
        return self._write_text_file(text_basename, payload)

    # -- fuentes -------------------------------------------------------------
    def _parse_font(self, block):
        # claves case-insensitive
        low = {k.lower(): v for k, v in block.items()}
        name = parse_string_value(low.get("name", "")) if "name" in low else None
        size = parse_number(low.get("size", "")) if "size" in low else None
        weight = parse_number(low.get("weight", "")) if "weight" in low else None
        underline = parse_bool(low["underline"]) if "underline" in low else False
        italic = parse_bool(low["italic"]) if "italic" in low else False
        strike = parse_bool(low["strikethrough"]) if "strikethrough" in low else False
        return {
            "name": name,
            "size": size,
            "bold": bool(weight and weight >= 700),
            "italic": bool(italic),
            "underline": bool(underline),
            "strikethrough": bool(strike),
        }

    # -- controles -----------------------------------------------------------
    def _build_control(self, node, form_name):
        c = {
            "type": node.vbtype,
            "name": node.name,
            "index": None,
            "x": None, "y": None, "w": None, "h": None,
            "caption": None, "text": None, "text_file": None, "picture": None,
            "font": None,
            "fore_color": None, "back_color": None, "back_style": None,
            "border_style": None, "alignment": None,
            "multiline": None, "scrollbars": None, "locked": None,
            "visible": None, "enabled": None,
            "auto_size": None, "word_wrap": None, "stretch": None,
            "interval": None, "tab_index": None,
            "children": [],
            "raw": {},
        }
        raw = c["raw"]
        if node.libclass and not node.libclass.startswith("VB."):
            raw["_ocx"] = node.libclass

        for prop, val in node.props.items():
            pl = prop.lower()
            if pl == "left":
                c["x"] = twips_to_px(parse_number(val) or 0)
            elif pl == "top":
                c["y"] = twips_to_px(parse_number(val) or 0)
            elif pl == "width":
                c["w"] = twips_to_px(parse_number(val) or 0)
            elif pl == "height":
                c["h"] = twips_to_px(parse_number(val) or 0)
            elif pl == "index":
                c["index"] = parse_number(val)
            elif pl == "tabindex":
                c["tab_index"] = parse_number(val)
            elif pl == "backstyle":
                c["back_style"] = parse_number(val)
            elif pl == "borderstyle":
                c["border_style"] = parse_number(val)
            elif pl == "alignment":
                c["alignment"] = parse_number(val)
            elif pl == "multiline":
                c["multiline"] = parse_bool(val)
            elif pl == "scrollbars":
                c["scrollbars"] = parse_number(val)
            elif pl == "locked":
                c["locked"] = parse_bool(val)
            elif pl == "visible":
                c["visible"] = parse_bool(val)
            elif pl == "enabled":
                c["enabled"] = parse_bool(val)
            elif pl == "autosize":
                c["auto_size"] = parse_bool(val)
            elif pl == "wordwrap":
                c["word_wrap"] = parse_bool(val)
            elif pl == "stretch":
                c["stretch"] = parse_bool(val)
            elif pl == "interval":
                c["interval"] = parse_number(val)
            elif pl in COLOR_PROPS:
                hexc, orig = parse_color(val)
                if pl == "forecolor":
                    c["fore_color"] = hexc
                elif pl == "backcolor":
                    c["back_color"] = hexc
                else:
                    raw[prop] = clean_scalar(val)
                raw["_color_%s" % pl] = orig.strip()
            elif pl in ("caption", "text"):
                self._assign_text(c, prop, val, form_name, node.name)
            elif pl in IMAGE_PROPS:
                self._assign_image(c, prop, val, form_name, node.name, raw)
            elif pl == "oleobjectblob":
                # blob OLE de un OCX: no se decodifica, se anota el ref.
                self.stats["frx_refs"] += 1
                raw["_oleobjectblob"] = clean_scalar(val)
            else:
                sv = parse_string_value(val)
                raw[prop] = sv if sv is not None else clean_scalar(val)

        # geometria de Line/Shape
        if node.vbtype == "Line":
            for k in ("X1", "Y1", "X2", "Y2"):
                if k in node.props:
                    raw[k.lower()] = twips_to_px(parse_number(node.props[k]) or 0)
        if node.vbtype == "Shape" and "Shape" in node.props:
            raw["shape"] = parse_number(node.props["Shape"])

        # fuente
        if "Font" in node.propblocks:
            c["font"] = self._parse_font(node.propblocks["Font"])
        # otros BeginProperty (p.ej. StatusBar Panels) -> raw
        for bn, inner in node.propblocks.items():
            if bn == "Font":
                continue
            raw["_propblock_%s" % bn] = {k: clean_scalar(v) for k, v in inner.items()}

        # hijos
        for ch in node.children:
            c["children"].append(self._build_control(ch, form_name))
            self.stats["controls"] += 1

        return c

    def _assign_text(self, container, prop, val, form_name, ctrl_name):
        """Asigna caption/text; texto largo o de FRX -> text/*.txt."""
        pl = prop.lower()
        ref = parse_frx_ref(val)
        if ref:
            frx_name, offset = ref
            base = "%s_%s.txt" % (form_name, ctrl_name)
            rel = self._extract_text_ref(frx_name, offset, base,
                                         "%s.%s.%s" % (form_name, ctrl_name, prop))
            if rel:
                container["text_file"] = rel
            return
        sv = parse_string_value(val)
        if sv is None:
            sv = clean_scalar(val)
        if sv is not None and len(sv) > INLINE_TEXT_LIMIT:
            base = "%s_%s.txt" % (form_name, ctrl_name)
            container["text_file"] = self._write_text_file(
                base, sv.encode(SRC_ENCODING, "replace"))
            return
        if pl == "caption":
            container["caption"] = sv
        else:
            container["text"] = sv

    def _assign_image(self, container, prop, val, form_name, ctrl_name, raw):
        pl = prop.lower()
        ref = parse_frx_ref(val)
        if ref:
            frx_name, offset = ref
            base = "%s.%s.%s.png" % (form_name, ctrl_name, pl)
            desc = "%s.%s.%s" % (form_name, ctrl_name, prop)
            rel = self._extract_image(frx_name, offset, base, desc)
            if pl == "picture":
                container["picture"] = rel
                if rel is None:
                    raw["_picture_frx"] = "%s:%04X" % (frx_name, offset)
            else:
                if rel:
                    raw["_%s" % pl] = rel
                else:
                    raw["_%s_frx" % pl] = "%s:%04X" % (frx_name, offset)
            return
        # referencia a archivo externo (bmp/ico suelto)
        sv = parse_string_value(val)
        if sv:
            real = self.src.resolve(sv)
            if real:
                base = "%s.%s.%s.png" % (form_name, ctrl_name, pl)
                data = self.src.read_bytes(sv)
                kind = _sniff_image(data) if data else None
                if kind:
                    ok, info = image_payload_to_png(
                        data, kind, self._asset_path(base))
                    if ok:
                        self.stats["images"] += 1
                        rel = self._rel_asset(base)
                        if pl == "picture":
                            container["picture"] = rel
                        else:
                            raw["_%s" % pl] = rel
                        return
            raw[prop] = sv

    # -- form ----------------------------------------------------------------
    def _build_form(self, root, form_name):
        f = {
            "file": None,  # relleno por el caller
            "type": root.vbtype,
            "caption": None,
            "client_w": None, "client_h": None,
            "border_style": None,
            "max_button": None, "min_button": None,
            "back_color": None, "fore_color": None,
            "icon": None, "picture": None,
            "font": None,
            "controls": [],
            "menu": [],
            "code": "",
            "raw": {},
        }
        raw = f["raw"]
        for prop, val in root.props.items():
            pl = prop.lower()
            if pl == "caption":
                f["caption"] = parse_string_value(val)
            elif pl == "clientwidth":
                f["client_w"] = twips_to_px(parse_number(val) or 0)
            elif pl == "clientheight":
                f["client_h"] = twips_to_px(parse_number(val) or 0)
            elif pl == "borderstyle":
                f["border_style"] = parse_number(val)
            elif pl == "maxbutton":
                f["max_button"] = parse_bool(val)
            elif pl == "minbutton":
                f["min_button"] = parse_bool(val)
            elif pl == "backcolor":
                hexc, orig = parse_color(val)
                f["back_color"] = hexc
                raw["_color_backcolor"] = orig.strip()
            elif pl == "forecolor":
                hexc, orig = parse_color(val)
                f["fore_color"] = hexc
                raw["_color_forecolor"] = orig.strip()
            elif pl in ("icon", "picture"):
                ref = parse_frx_ref(val)
                if ref:
                    frx_name, offset = ref
                    base = "%s.%s.png" % (form_name, pl)
                    rel = self._extract_image(
                        frx_name, offset, base, "%s.%s" % (form_name, prop))
                    if pl == "icon":
                        f["icon"] = rel
                    else:
                        f["picture"] = rel
                    if rel is None and pl == "picture":
                        raw["_picture_frx"] = "%s:%04X" % (frx_name, offset)
                    elif rel is None and pl == "icon":
                        raw["_icon_frx"] = "%s:%04X" % (frx_name, offset)
            else:
                sv = parse_string_value(val)
                raw[prop] = sv if sv is not None else clean_scalar(val)

        # defaults VB para forms
        if f["type"] != "MDIForm":
            if f["border_style"] is None:
                f["border_style"] = 2  # Sizable (default VB)
            if f["max_button"] is None:
                f["max_button"] = True
            if f["min_button"] is None:
                f["min_button"] = True

        if "Font" in root.propblocks:
            f["font"] = self._parse_font(root.propblocks["Font"])

        # separar controles y menus
        for ch in root.children:
            if ch.vbtype == "Menu":
                f["menu"].append(self._build_menu(ch))
                self.stats["menus"] += 1
            else:
                f["controls"].append(self._build_control(ch, form_name))
                self.stats["controls"] += 1
        return f

    def _build_menu(self, node):
        m = {"name": node.name, "caption": None, "children": []}
        for prop, val in node.props.items():
            pl = prop.lower()
            if pl == "caption":
                m["caption"] = parse_string_value(val)
            elif pl == "shortcut":
                m["shortcut"] = clean_scalar(val)
            elif pl == "index":
                m["index"] = parse_number(val)
            elif pl in ("checked", "enabled", "visible", "windowlist"):
                b = parse_bool(val)
                # solo emitir si difiere del default (enabled/visible=True)
                if pl in ("checked", "windowlist") and b:
                    m[pl] = True
                elif pl in ("enabled", "visible") and b is False:
                    m[pl] = False
        for ch in node.children:
            if ch.vbtype == "Menu":
                m["children"].append(self._build_menu(ch))
                self.stats["menus"] += 1
        return m

    # -- run ----------------------------------------------------------------
    def run(self):
        # limpieza idempotente
        if os.path.isdir(self.out):
            shutil.rmtree(self.out)
        os.makedirs(self.assets, exist_ok=True)
        os.makedirs(self.textdir, exist_ok=True)

        vbp_name = None
        for name in os.listdir(self.src.path):
            if name.lower().endswith(".vbp"):
                vbp_name = name
                break
        if not vbp_name:
            raise RuntimeError("No .vbp en %s" % self.issue)
        vbp_text = dsrc(self.src.read_bytes(vbp_name))

        def vbp_get(key):
            mm = re.search(r"^%s=(.*)$" % re.escape(key), vbp_text, re.M)
            return mm.group(1).strip() if mm else None

        def unq(s):
            if s and s.startswith('"') and s.endswith('"'):
                return s[1:-1]
            return s

        form_files = re.findall(r"^Form=(.*)$", vbp_text, re.M)

        forms = {}
        form_order = []
        file_to_vbname = {}

        # Pre-pass: registrar todos los offsets .frx para poder acotar records.
        resolved_forms = []
        for ff in form_files:
            ff = ff.strip()
            real = self.src.resolve(ff)
            if real is None:
                self.stats["missing_forms"].append(ff)
                continue
            text = dsrc(self.src.read_bytes(real))
            self._scan_frx_offsets(text)
            resolved_forms.append((real, text))
        for key, offs in self._frx_offsets.items():
            self._frx_offsets[key] = sorted(offs)

        for real, text in resolved_forms:
            root, version, code = parse_frm(text)
            if root is None:
                self.stats["anomalies"].append("Form sin Begin: %s" % real)
                continue
            vbname = get_vb_name(root, text)
            fobj = self._build_form(root, vbname)
            fobj["file"] = real
            fobj["code"] = code
            forms[vbname] = fobj
            form_order.append(vbname)
            file_to_vbname[norm_name(real)] = vbname
            file_to_vbname[norm_name(os.path.splitext(real)[0])] = vbname
            self.stats["forms"] += 1

        # startup: Startup -> IconForm -> primer Form
        def resolve_form_ref(ref):
            if not ref:
                return None
            ref = unq(ref)
            if ref in forms:            # nombre interno directo
                return ref
            key = norm_name(ref)
            if key in file_to_vbname:   # nombre de archivo
                return file_to_vbname[key]
            key2 = norm_name(ref + ".frm")
            if key2 in file_to_vbname:
                return file_to_vbname[key2]
            return None

        startup = (resolve_form_ref(vbp_get("Startup"))
                   or resolve_form_ref(vbp_get("IconForm"))
                   or (form_order[0] if form_order else None))

        # version del numero: del primer form parseado (o Form1)
        vb_version = 4
        first_file = self.src.resolve("Form1.frm") or (
            self.src.resolve(form_files[0]) if form_files else None)
        if first_file:
            ft = dsrc(self.src.read_bytes(first_file))
            fl = ft.split("\n", 1)[0]
            mver = re.search(r"VERSION\s+(\d+)", fl)
            if mver:
                vb_version = int(mver.group(1))

        manifest = {
            "issue_id": self.issue,
            "title": unq(vbp_get("Title")),
            "version_comments": unq(vbp_get("VersionComments")),
            "vb_version": vb_version,
            "startup_form": startup,
            "form_order": form_order,
            "forms": forms,
        }

        with open(os.path.join(self.out, "manifest.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)

        return self.stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Extractor VB -> data/ (Fase 1 ERN)")
    ap.add_argument("--issue", help="numero concreto, p.ej. ERNSC1-1")
    ap.add_argument("--all", action="store_true", help="procesa los 10 numeros")
    args = ap.parse_args(argv)

    if args.issue:
        targets = [args.issue]
    elif args.all:
        targets = ISSUES
    else:
        ap.error("indica --all o --issue <ISSUE>")
        return 2

    os.makedirs(DATA_ROOT, exist_ok=True)
    grand_unresolved = 0
    print("%-10s %6s %8s %6s %6s %6s %s" %
          ("ISSUE", "forms", "controls", "menus", "texts", "imgs", "notas"))
    for issue in targets:
        ex = IssueExtractor(issue)
        st = ex.run()
        grand_unresolved += st["frx_unresolved"]
        notes = []
        if st["missing_forms"]:
            notes.append("forms ausentes=%d" % len(st["missing_forms"]))
        if st["metafiles_skipped"]:
            notes.append("metafiles=%d" % st["metafiles_skipped"])
        if st["frx_unresolved"]:
            notes.append("FRX_SIN_RESOLVER=%d" % st["frx_unresolved"])
        print("%-10s %6d %8d %6d %6d %6d %s" %
              (issue, st["forms"], st["controls"], st["menus"],
               st["texts"], st["images"], ", ".join(notes)))

    if grand_unresolved:
        print("\nADVERTENCIA: %d referencias FRX sin resolver" % grand_unresolved)
    return 0


if __name__ == "__main__":
    sys.exit(main())
