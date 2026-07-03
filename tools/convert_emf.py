#!/usr/bin/env python3
"""Post-proceso de la Fase 1: rasteriza los fondos EMF que Pillow no soporta.

Busca en los manifests forms con picture=null y raw._picture_frx, extrae el
payload del .frx (cabecera de 12 bytes: [u32 recsize]["lt"][u16 00][u32 imgsize]),
lo convierte a PNG con LibreOffice headless y actualiza el manifest.

Requiere: libreoffice en PATH. Uso: python3 tools/convert_emf.py
"""
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def extract_frx_image(frx_path: Path, offset: int) -> bytes | None:
    data = frx_path.read_bytes()
    if offset + 12 > len(data):
        return None
    recsize, tag, _pad, imgsize = struct.unpack_from("<I2sHI", data, offset)
    if tag != b"lt" or imgsize == 0:
        return None
    payload = data[offset + 12 : offset + 12 + imgsize]
    return payload if len(payload) == imgsize else None


def main() -> int:
    pending = []  # (manifest_path, form_name, emf_tmp_path)
    tmpdir = Path(tempfile.mkdtemp(prefix="ern_emf_"))
    for manifest_path in sorted(DATA.glob("ERNSC*/manifest.json")):
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        issue_dir = ROOT / m["issue_id"]
        for fname, form in m["forms"].items():
            ref = (form.get("raw") or {}).get("_picture_frx")
            if form.get("picture") or not ref:
                continue
            frx_file, off_hex = ref.rsplit(":", 1)
            payload = extract_frx_image(issue_dir / frx_file, int(off_hex, 16))
            if payload is None:
                print(f"[WARN] {m['issue_id']}/{fname}: record vacío o ilegible ({ref})")
                continue
            sig = payload[40:44] if len(payload) > 44 else b""
            ext = ".emf" if sig == b" EMF" else ".wmf"
            tmp = tmpdir / f"{m['issue_id']}__{fname}{ext}"
            tmp.write_bytes(payload)
            pending.append((manifest_path, fname, tmp))

    if not pending:
        print("Nada que convertir.")
        return 0

    subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "png", "--outdir", str(tmpdir)]
        + [str(t) for _, _, t in pending],
        check=True, capture_output=True, timeout=300,
    )

    failures = 0
    for manifest_path, fname, tmp in pending:
        png = tmp.with_suffix(".png")
        if not png.exists():
            print(f"[FAIL] sin PNG para {tmp.name}")
            failures += 1
            continue
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        rel = f"assets/{fname}.picture.png"
        dest = manifest_path.parent / rel
        dest.write_bytes(png.read_bytes())
        m["forms"][fname]["picture"] = rel
        manifest_path.write_text(
            json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        from PIL import Image
        with Image.open(dest) as im:
            f = m["forms"][fname]
            print(f"[OK] {m['issue_id']}/{fname}: {im.size[0]}x{im.size[1]} px "
                  f"(form client {f['client_w']}x{f['client_h']})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
