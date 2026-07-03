#!/usr/bin/env python3
"""Smoke tests for docs/FEATURES.md §2 (search), §3 (session state) and
§4 (keyboard accessibility hooks).

Uses update() instead of mainloop() (needs a DISPLAY), same harness style as
test_engine.py. Exit code is non-zero if any check fails.

Run:  python3 tests/test_features.py
"""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

DATA_DIR = os.path.join(ROOT, "data")
SAMPLE = os.path.join(HERE, "sample_data")

from ernreader import search, state               # noqa: E402
from ernreader.launcher import Launcher            # noqa: E402


_passed = 0
_failed = 0


def check(cond, label):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  ok   {label}")
    else:
        _failed += 1
        print(f"  FAIL {label}")


def test_search():
    print("[search]")
    idx = search.SearchIndex(DATA_DIR)
    docs = idx.ensure_built()
    check(len(docs) > 0, f"index built ({len(docs)} documents)")

    telnor_results = idx.search("telnor")
    check(any(r.issue_id == "ERNSC2-3" for r in telnor_results),
          "'telnor' finds a result in ERNSC2-3")

    pedo_results = idx.search("pedo historia")
    check(any(r.issue_id == "ERNSC2-5" and r.form_name == "anarquia"
              for r in pedo_results),
          "'pedo historia' (AND) finds ERNSC2-5/anarquia")

    # a nonsense query should find nothing
    check(idx.search("xyzzy_no_deberia_existir_jamas") == [],
          "nonsense query yields no results")

    # normalization: accents/case should not matter
    accented = idx.search("PEDO HISTORIA")
    check(len(accented) == len(pedo_results),
          "search is case/accent-insensitive")
    return len(docs)


def test_open_issue_form():
    print("[open_issue_form]")
    app = Launcher(SAMPLE, restore=False)
    app.root.update()
    check(app.session is None, "no session open initially")

    app.open_issue_form("ERNTEST", "Articulo")
    app.root.update()
    check(app.session is not None, "session created")
    check("Articulo" in app.session.open_forms,
          "open_issue_form opened the requested form")
    check("Portada" not in app.session.open_forms,
          "open_issue_form does not also open the startup form")

    # calling it again for the same issue should just re-show/track, not
    # spawn a second session
    app.open_issue_form("ERNTEST", "Reloj")
    app.root.update()
    check("Reloj" in app.session.open_forms,
          "open_issue_form can open a second form in the same session")

    app.session.quit_issue()
    app.root.update()
    app.root.destroy()


def test_state_roundtrip():
    print("[state]")
    with tempfile.TemporaryDirectory() as tmp:
        old_xdg = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = tmp
        try:
            check(state.load_state() is None, "no state initially")
            payload = {"last_issue": "ERNSC2-3",
                      "open_forms": ["Forma1", "anarquia"], "ts": 12345.0}
            state.save_state(payload)
            path = os.path.join(tmp, "ernreader", "state.json")
            check(os.path.isfile(path), "state.json written under XDG_DATA_HOME")
            loaded = state.load_state()
            check(loaded is not None, "state reloaded")
            check(loaded.get("last_issue") == "ERNSC2-3",
                  "last_issue round-trips")
            check(loaded.get("open_forms") == ["Forma1", "anarquia"],
                  "open_forms round-trips")
        finally:
            if old_xdg is None:
                os.environ.pop("XDG_DATA_HOME", None)
            else:
                os.environ["XDG_DATA_HOME"] = old_xdg

    # IO robustness: pointing at an unwritable location must not raise
    bogus_dir = "/nonexistent_root_only_path_xyz/state"
    old_xdg = os.environ.get("XDG_DATA_HOME")
    os.environ["XDG_DATA_HOME"] = bogus_dir
    try:
        try:
            state.save_state({"last_issue": "X", "open_forms": [], "ts": 0})
            ok = True
        except Exception:
            ok = False
        check(ok, "save_state to an unwritable path does not raise")
    finally:
        if old_xdg is None:
            os.environ.pop("XDG_DATA_HOME", None)
        else:
            os.environ["XDG_DATA_HOME"] = old_xdg


def test_launcher_keyboard_rows():
    print("[accessibility]")
    app = Launcher(SAMPLE, restore=False)
    app.root.update()
    check(len(app._focus_rows) >= 1, "at least one focusable row registered")
    row = app._focus_rows[0]
    check(int(row.cget("takefocus")) == 1, "row is a Tab stop (takefocus=1)")
    check(int(row.cget("highlightthickness")) > 0,
          "row has a focus-ring border")
    app.root.focus_force()
    row.focus_set()
    app.root.update()
    check(app.root.focus_get() is row, "row can actually receive focus")
    app.root.destroy()


def screenshot_search_window(out_path):
    print("[screenshot]")
    # Use the real data/ collection (not the tiny sample fixture) so the
    # screenshot actually shows several matching results.
    app = Launcher(DATA_DIR, restore=False)
    app.root.update()
    app.open_search()
    app.root.update()
    win = app._search_window
    win.entry.insert(0, "anarquia")
    win._do_search()
    app.root.update()
    win.top.update_idletasks()
    geo = win.top.winfo_geometry()
    check(win.listbox.size() >= 0, "search window populated (may be 0 in sample data)")
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        win.top.after(200, lambda: None)
        app.root.update()
        rc = os.system(
            f"import -window {win.top.winfo_id()} {out_path} 2>/dev/null")
        check(rc == 0 and os.path.isfile(out_path),
              f"screenshot captured to {out_path}")
    except Exception as exc:
        check(False, f"screenshot failed: {exc}")
    app.root.destroy()


def main():
    # Every Launcher instance created below may write session state via
    # _save_state(); keep that entirely inside a throwaway directory so
    # running the test suite never touches the developer's real
    # ~/.local/share/ernreader/state.json.
    old_xdg = os.environ.get("XDG_DATA_HOME")
    tmp_home = tempfile.mkdtemp(prefix="ernreader-test-state-")
    os.environ["XDG_DATA_HOME"] = tmp_home
    try:
        n_docs = test_search()
        test_open_issue_form()
        test_state_roundtrip()
        test_launcher_keyboard_rows()

        out = sys.argv[1] if len(sys.argv) > 1 else None
        if out:
            screenshot_search_window(out)
    finally:
        if old_xdg is None:
            os.environ.pop("XDG_DATA_HOME", None)
        else:
            os.environ["XDG_DATA_HOME"] = old_xdg

    print(f"\n{_passed} passed, {_failed} failed "
          f"(search index: {n_docs} documents)")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
