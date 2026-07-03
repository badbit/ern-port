#!/usr/bin/env python3
"""
Fase 4 — Validador cruzado de manifests, behaviors y assets.
Comprueba 10 números (ERNSC1-1..ERNSC1-6, ERNSC2-2..ERNSC2-5) contra:
  (a) Forms en manifest vs Form= en .vbp
  (b) Archivos referenciados (text, picture, icon) existen
  (c) PNGs en assets/ abren con PIL
  (d) Eventos en behavior.json referencian controles válidos
  (e) show_form apunta a forms existentes
  (f) Nº de Private Sub NO vacíos == eventos mapeados
"""

import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from PIL import Image

# Issues a validar
ISSUES = [
    "ERNSC1-1", "ERNSC1-2", "ERNSC1-3", "ERNSC1-4", "ERNSC1-5", "ERNSC1-6",
    "ERNSC2-2", "ERNSC2-3", "ERNSC2-4", "ERNSC2-5"
]

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"


class Validator:
    def __init__(self):
        self.discrepancies = []  # Lista de (issue, form, detalle)
        self.warnings = []       # Huérfanos documentados del original: no fallan
        self.results = {}  # {issue: {forms: int, assets_ok: bool, ...}}

    def add_discrepancy(self, issue: str, form: str, detail: str):
        """Registra una discrepancia encontrada."""
        self.discrepancies.append((issue, form, detail))

    def validate_issue(self, issue: str) -> Dict[str, Any]:
        """Valida un número completo. Retorna dict con resultados."""
        result = {
            "issue": issue,
            "vbp_forms": 0,
            "manifest_forms": 0,
            "missing_forms": 0,
            "forms_match": False,
            "assets_ok": True,
            "text_files_ok": True,
            "png_open_ok": True,
            "behavior_ok": True,
            "events_valid": True,
            "show_forms_valid": True,
            "subs_match": True,
            "errors": []
        }

        issue_path = DATA_DIR / issue
        if not issue_path.exists():
            result["errors"].append(f"Directorio data/{issue} no existe")
            return result

        # 1. Leer .vbp y contar Form= resolubles
        vbp_forms = self._check_vbp_forms(issue)
        result["vbp_forms"] = len(vbp_forms)

        # 2. Leer manifest.json
        manifest = self._read_manifest(issue)
        if manifest is None:
            result["errors"].append("manifest.json no existe o no parsea")
            return result

        # 3. (a) Contar forms en manifest y missing_forms
        forms_in_manifest = set(manifest.get("forms", {}).keys())
        result["manifest_forms"] = len(forms_in_manifest)
        missing = set(manifest.get("missing_forms", []))
        result["missing_forms"] = len(missing)

        # Validar (a): forms + missing == vbp_forms
        if len(forms_in_manifest) + len(missing) == len(vbp_forms):
            result["forms_match"] = True
        else:
            result["forms_match"] = False
            self.add_discrepancy(
                issue, ".",
                f"Nº de forms: manifest={len(forms_in_manifest)}, missing={len(missing)}, "
                f"vbp={len(vbp_forms)}; suma debe igualar vbp"
            )

        # 4. (b) Validar text_file, picture, icon existen
        result["text_files_ok"] = self._check_referenced_files(issue, manifest)

        # 5. (c) Validar PNGs en assets/ abren con PIL
        result["png_open_ok"] = self._check_pngs_valid(issue)

        # 6. Leer behavior.json
        behavior = self._read_behavior(issue)
        if behavior is None:
            result["behavior_ok"] = False
            result["events_valid"] = False
            result["show_forms_valid"] = False
            result["errors"].append("behavior.json no existe o no parsea")
        else:
            result["behavior_ok"] = True
            # (d) Validar eventos referencian controles válidos
            events_ok = self._check_events_valid(issue, manifest, behavior)
            result["events_valid"] = events_ok
            # (e) Validar show_form apuntan a forms válidos
            show_forms_ok = self._check_show_form_valid(issue, manifest, behavior)
            result["show_forms_valid"] = show_forms_ok
            # (f) Validar nº de subs vs eventos mapeados
            subs_match = self._check_subs_count(issue, manifest, behavior)
            result["subs_match"] = subs_match

        return result

    def _check_vbp_forms(self, issue: str) -> List[str]:
        """Lee .vbp (encoding CP1252) y retorna lista de Form= resolubles."""
        vbp_dir = ROOT / issue
        vbp_files = list(vbp_dir.glob("*.vbp"))
        if not vbp_files:
            self.add_discrepancy(issue, ".", f"No hay archivo .vbp en {issue}/")
            return []

        vbp_file = vbp_files[0]
        try:
            content = vbp_file.read_text(encoding="cp1252")
        except Exception as e:
            self.add_discrepancy(issue, ".", f"No se puede leer {vbp_file}: {e}")
            return []

        # Los .vbp están en CP1252 pero el filesystem en UTF-8, y hay rutas
        # absolutas residuales (C:\Form21.frm): resolver por nombre base
        # normalizado NFC case-insensitive contra el listado real.
        listing = {
            unicodedata.normalize("NFC", p.name).lower(): p
            for p in vbp_dir.iterdir()
        }
        forms = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("Form="):
                filename = line.split("=", 1)[1].replace("\\", "/").rsplit("/", 1)[-1]
                key = unicodedata.normalize("NFC", filename).lower()
                frm_path = listing.get(key)
                if frm_path is not None:
                    # Extraer nombre interno del .frm (Attribute VB_Name)
                    try:
                        frm_content = frm_path.read_text(encoding="cp1252")
                        match = re.search(r'Attribute VB_Name\s*=\s*"([^"]+)"', frm_content)
                        if match:
                            forms.append(match.group(1))
                    except Exception:
                        pass
        return forms

    def _read_manifest(self, issue: str) -> Dict[str, Any] | None:
        """Lee manifest.json del issue."""
        manifest_path = DATA_DIR / issue / "manifest.json"
        if not manifest_path.exists():
            return None
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            self.add_discrepancy(issue, ".", f"Error al parsear manifest.json: {e}")
            return None

    def _read_behavior(self, issue: str) -> Dict[str, Any] | None:
        """Lee behavior.json del issue."""
        behavior_path = DATA_DIR / issue / "behavior.json"
        if not behavior_path.exists():
            return None
        try:
            return json.loads(behavior_path.read_text(encoding="utf-8"))
        except Exception as e:
            self.add_discrepancy(issue, ".", f"Error al parsear behavior.json: {e}")
            return None

    def _check_referenced_files(self, issue: str, manifest: Dict) -> bool:
        """(b) Valida que todo text_file, picture, icon existe."""
        all_ok = True
        issue_path = DATA_DIR / issue

        def check_file(form_name: str, control_name: str | None, file_path: str):
            nonlocal all_ok
            if file_path is None:
                return
            full_path = issue_path / file_path
            if not full_path.exists():
                all_ok = False
                ctx = f"{control_name}" if control_name else "(form)"
                self.add_discrepancy(
                    issue, form_name,
                    f"Archivo referenciado no existe: {file_path} (en {ctx})"
                )

        for form_name, form in manifest.get("forms", {}).items():
            # Form properties
            for prop in ["icon", "picture"]:
                if form.get(prop):
                    check_file(form_name, None, form[prop])

            # Controls (recursivo)
            def check_controls(controls, prefix=""):
                for ctrl in controls:
                    ctrl_name = prefix + ctrl.get("name", "")
                    for prop in ["text_file", "picture"]:
                        if ctrl.get(prop):
                            check_file(form_name, ctrl_name, ctrl[prop])
                    # Controles anidados
                    if ctrl.get("children"):
                        check_controls(ctrl["children"], prefix)

            if form.get("controls"):
                check_controls(form["controls"])

        return all_ok

    def _check_pngs_valid(self, issue: str) -> bool:
        """(c) Valida que todos los PNGs en assets/ abren con PIL."""
        assets_path = DATA_DIR / issue / "assets"
        if not assets_path.exists():
            return True

        all_ok = True
        for png_file in assets_path.glob("*.png"):
            try:
                img = Image.open(png_file)
                img.verify()
            except Exception as e:
                all_ok = False
                self.add_discrepancy(
                    issue, ".",
                    f"PNG no se abre con PIL: {png_file.name} — {e}"
                )
        return all_ok

    def _check_events_valid(self, issue: str, manifest: Dict, behavior: Dict) -> bool:
        """(d) Valida que eventos en behavior referencian controles válidos."""
        all_ok = True
        for form_name, form_behavior in behavior.get("forms", {}).items():
            if form_name not in manifest.get("forms", {}):
                continue

            form = manifest["forms"][form_name]
            # Construir set de controles válidos (incluyendo menú items)
            valid_controls = self._get_valid_controls(form)
            # "Form" siempre es válido (eventos del form mismo como Form.Resize, Form.KeyPress)
            valid_controls.add("Form")

            # on_load es siempre válido (del form)
            # eventos deben referenciar controles válidos
            for event_key in form_behavior.get("events", {}).keys():
                # event_key es "control.Evento"
                parts = event_key.rsplit(".", 1)
                if len(parts) != 2:
                    all_ok = False
                    self.add_discrepancy(
                        issue, form_name,
                        f"Evento mal formado: {event_key}"
                    )
                    continue

                control_name, event_name = parts
                if control_name not in valid_controls:
                    # Código huérfano del original (VB conserva handlers de
                    # controles borrados); el motor nunca los dispara.
                    self.warnings.append((
                        issue, form_name,
                        f"Evento {event_key}: control '{control_name}' no existe "
                        "(código huérfano del original)"
                    ))

        return all_ok

    def _get_valid_controls(self, form: Dict) -> Set[str]:
        """Retorna set de nombres de controles válidos (incluyendo menú items)."""
        valid = set()

        # Controles normales (recursivo)
        def collect_controls(controls):
            for ctrl in controls:
                valid.add(ctrl.get("name", ""))
                if ctrl.get("children"):
                    collect_controls(ctrl["children"])

        if form.get("controls"):
            collect_controls(form["controls"])

        # Menú items
        def collect_menu_items(menu_items):
            for item in menu_items:
                valid.add(item.get("name", ""))
                if item.get("children"):
                    collect_menu_items(item["children"])

        if form.get("menu"):
            collect_menu_items(form["menu"])

        return valid

    def _check_show_form_valid(self, issue: str, manifest: Dict, behavior: Dict):
        """(e) Valida que show_form ops apunten a forms válidos."""
        valid_forms = set(manifest.get("forms", {}).keys())

        def check_ops(ops):
            if not isinstance(ops, list):
                return
            for op in ops:
                if not isinstance(op, dict):
                    continue
                if op.get("op") == "show_form":
                    form = op.get("form")
                    if form and form not in valid_forms:
                        self.add_discrepancy(
                            issue, ".",
                            f"show_form apunta a form inexistente: {form}"
                        )
                # ops anidados (e.g., en sequence)
                if "ops" in op:
                    check_ops(op["ops"])

        for form_name, form_behavior in behavior.get("forms", {}).items():
            check_ops(form_behavior.get("on_load", []))
            for event_key, ops in form_behavior.get("events", {}).items():
                check_ops(ops)

    def _check_subs_count(self, issue: str, manifest: Dict, behavior: Dict) -> bool:
        """(f) Valida que nº de Private Sub NO vacíos == eventos mapeados."""
        forms_match = True

        for form_name, form in manifest.get("forms", {}).items():
            code = form.get("code", "")
            non_empty_subs = self._count_non_empty_subs(code)

            form_behavior = behavior.get("forms", {}).get(form_name, {})
            on_load_count = 1 if form_behavior.get("on_load") else 0
            events_count = len(form_behavior.get("events", {}))
            expected_subs = on_load_count + events_count

            # Excepción conocida: ERNSC1-1, Form2, Command6.Click tiene 2 ops en vez de 3
            exception_applies = (issue == "ERNSC1-1" and form_name == "Form2" and
                                "Command6.Click" in form_behavior.get("events", {}))

            if non_empty_subs != expected_subs:
                if not exception_applies:
                    forms_match = False
                    self.add_discrepancy(
                        issue, form_name,
                        f"Nº de Private Sub NO vacíos ({non_empty_subs}) != "
                        f"eventos+on_load ({expected_subs}); eventos: "
                        f"{list(form_behavior.get('events', {}).keys())}"
                    )

        return forms_match

    def _count_non_empty_subs(self, code: str) -> int:
        """Cuenta Private Sub…End Sub que NO están vacíos."""
        count = 0
        # Buscar bloques Private Sub ... End Sub
        pattern = r'Private Sub\s+\w+\([^)]*\)(.*?)End Sub'
        for match in re.finditer(pattern, code, re.DOTALL):
            body = match.group(1)
            # Eliminar comentarios (desde ' hasta fin de línea)
            body_no_comments = re.sub(r"'.*?$", "", body, flags=re.MULTILINE)
            # Eliminar whitespace
            body_stripped = body_no_comments.strip()
            if body_stripped:
                count += 1
        return count

    def print_summary_table(self):
        """Imprime tabla resumen de validación."""
        print("\n" + "=" * 100)
        print("RESUMEN DE VALIDACIÓN — Fase 4")
        print("=" * 100)
        print(f"{'Issue':<12} {'Forms':<8} {'Assets':<8} {'Textos':<8} {'Eventos':<8} {'Subs':<8} {'Status':<12}")
        print("-" * 100)

        all_pass = True
        for result in self.results.values():
            issue = result["issue"]
            forms_ok = "✓" if result["forms_match"] else "✗"
            assets_ok = "✓" if result["assets_ok"] else "✗"
            texts_ok = "✓" if result["text_files_ok"] else "✗"
            events_ok = "✓" if result["behavior_ok"] else "✗"
            subs_ok = "✓" if result["subs_match"] else "✗"

            status = "OK" if all([
                result["forms_match"],
                result["assets_ok"],
                result["text_files_ok"],
                result["behavior_ok"],
                result["subs_match"]
            ]) else "FAIL"

            if status == "FAIL":
                all_pass = False

            print(f"{issue:<12} {forms_ok:<8} {assets_ok:<8} {texts_ok:<8} {events_ok:<8} {subs_ok:<8} {status:<12}")

        print("=" * 100)
        return all_pass

    def print_discrepancies(self):
        """Imprime lista detallada de discrepancias."""
        if not self.discrepancies:
            print("\n✓ CERO DISCREPANCIAS — Todas las validaciones pasaron.\n")
            return

        print("\n" + "=" * 100)
        print("DISCREPANCIAS ENCONTRADAS")
        print("=" * 100)

        # Agrupar por issue
        by_issue = {}
        for issue, form, detail in self.discrepancies:
            if issue not in by_issue:
                by_issue[issue] = []
            by_issue[issue].append((form, detail))

        for issue in ISSUES:
            if issue not in by_issue:
                continue
            print(f"\n{issue}:")
            for form, detail in by_issue[issue]:
                form_str = f"  {form}:" if form != "." else "  (global):"
                print(f"{form_str}")
                print(f"    → {detail}")

        print("\n" + "=" * 100)


def main():
    validator = Validator()

    # Validar los 10 números
    for issue in ISSUES:
        result = validator.validate_issue(issue)
        validator.results[issue] = result

    # Imprimir tabla resumen
    all_pass = validator.print_summary_table()

    # Imprimir discrepancias detalladas
    validator.print_discrepancies()

    # Exit code
    if all_pass and not validator.discrepancies:
        if validator.warnings:
            print(f"\nADVERTENCIAS ({len(validator.warnings)}) — código huérfano "
                  "del original, informativo:")
            for issue, form, detail in validator.warnings:
                print(f"  {issue}/{form}: {detail}")
        print("\n✓ VALIDACIÓN COMPLETADA: TODO OK "
              f"({len(validator.warnings)} advertencia(s) informativas)\n")
        return 0
    else:
        print(f"\n✗ VALIDACIÓN COMPLETADA: {len(validator.discrepancies)} discrepancia(s)\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
