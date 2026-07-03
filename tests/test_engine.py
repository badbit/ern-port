#!/usr/bin/env python3
"""Headless-ish smoke tests for the ernreader engine and launcher.

Runs against tests/sample_data/ERNTEST. Uses update() instead of mainloop() so
it never blocks; blocking ops (msgbox, save dialog, browser) are stubbed. Every
form is built, inspected and destroyed, and we assert no stray stderr noise and
no dangling Toplevels remain.

Run:  python3 tests/test_engine.py      (needs a DISPLAY)
Exit code is non-zero if any check fails.
"""

import io
import os
import sys
import tempfile
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

SAMPLE = os.path.join(HERE, "sample_data")

from ernreader import actions, engine, theme            # noqa: E402
from ernreader.launcher import Launcher, parse_comments  # noqa: E402


# --- tiny test harness -------------------------------------------------------
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


# --- stubs for blocking dialogs ---------------------------------------------
class _FakeMsg:
    calls = []

    @staticmethod
    def showinfo(t, m, **k):
        _FakeMsg.calls.append(("info", t, m))
        return "ok"

    @staticmethod
    def showwarning(t, m, **k):
        _FakeMsg.calls.append(("warn", t, m))
        return "ok"

    @staticmethod
    def showerror(t, m, **k):
        _FakeMsg.calls.append(("error", t, m))
        return "ok"


class _FakeBrowser:
    opened = []

    @staticmethod
    def open(url, *a, **k):
        _FakeBrowser.opened.append(url)
        return True


_save_target = {"path": ""}


def _fake_saveas(**kwargs):
    return _save_target["path"]


def main():
    # install stubs
    actions.messagebox = _FakeMsg
    actions.webbrowser = _FakeBrowser
    actions.filedialog.asksaveasfilename = _fake_saveas

    # 1) launcher discovery -------------------------------------------------
    print("[launcher]")
    app = Launcher(SAMPLE)
    app.root.update()
    check(len(app.issues) == 1, "one issue discovered")
    issue = app.issues[0]
    check(issue["id"] == "ERNTEST", "issue id parsed")
    check(issue["title"] == "El Radiaktivo Newz (TEST)", "issue title")
    check(issue["date"] == "Julio 1999", "date parsed from version_comments")
    hl, dt = parse_comments("El Radiactivo News, Agosto 1998. Número 1, Año I")
    check(dt == "Agosto 1998", "parse_comments date")
    check(hl == "El Radiactivo News", "parse_comments headline")
    # launcher list frame has one row per issue (row + separator widgets)
    rows = app._list_frame.winfo_children()
    check(len(rows) >= 1, "launcher rendered issue rows")

    # 2) build the session on the launcher root -----------------------------
    print("[session/forms]")
    stderr_buf = io.StringIO()
    closed = {"n": 0}

    with contextlib.redirect_stderr(stderr_buf):
        sess = engine.IssueSession(app.root, issue["dir"], issue["manifest"],
                                   on_closed=lambda s: closed.__setitem__(
                                       "n", closed["n"] + 1))
        sess.start()
        app.root.update()

        portada = sess.open_forms.get("Portada")
        check(portada is not None, "startup form Portada opened")
        check(str(portada.top.title()).startswith("BadBit"), "Portada caption")
        # geometry
        app.root.update_idletasks()
        check(portada.top.winfo_reqwidth() == 400 or
              portada.top.winfo_width() in (400, 1), "Portada width ~400")
        # controls registered (incl. nested frame/picturebox children)
        for cname in ("cmdArticulo", "lblTitle", "imgLogo", "chkModo",
                      "optA", "optB", "lblInPic", "cmdSalir"):
            w, meta = portada.find_control(cname)
            check(cname in portada.controls, f"control registered: {cname}")
        # Line/Shape are canvas items, not widgets: verify they were drawn
        check(len(portada.base_canvas.find_all()) >= 2,
              "Line + Shape drawn on base canvas (bg image + primitives)")
        # image refs kept alive (icon + picture + logo at least)
        check(len(portada._images) >= 3, "Portada keeps image refs")
        # a button is really a Button, label a Label
        btn, _ = portada.find_control("cmdArticulo")
        check(btn.winfo_class() == "Button", "cmdArticulo is a Button")
        lbl, _ = portada.find_control("lblTitle")
        check(lbl.winfo_class() == "Label", "lblTitle is a Label")
        check(lbl.cget("wraplength") == 360, "lblTitle wraplength applied")

        # 3) Articulo: Text + scrollbars + menu -----------------------------
        art = sess.show_form("Articulo")
        app.root.update()
        check(art is not None and "Articulo" in sess.open_forms, "Articulo opened")
        txt, _ = art.find_control("txtBody")
        check(txt.winfo_class() == "Text", "txtBody is a Text")
        body = txt.get("1.0", "end-1c")
        check("ANARQUIA DIGITAL" in body, "txtBody loaded from text_file")
        check(str(txt.cget("state")) == "disabled", "txtBody is read-only")
        entry, _ = art.find_control("txtBusca")
        check(entry.winfo_class() == "Entry", "single-line TextBox -> Entry")
        lst, _ = art.find_control("lstSec")
        check(lst.winfo_class() == "Listbox", "ListBox -> Listbox")
        # menu attached
        check(bool(art.top.cget("menu")), "Articulo has a menu bar")

        # 4) Reloj: timers + clock/move ops ---------------------------------
        reloj = sess.show_form("Reloj")
        app.root.update()
        check(len(reloj._timers) == 2, "Reloj scheduled two timers")
        tlbl, _ = reloj.find_control("lblTime")
        # on_load ran clock already
        import re
        check(re.match(r"\d\d:\d\d:\d\d", tlbl.cget("text")) is not None,
              "clock op set lblTime")
        dlbl, _ = reloj.find_control("lblDate")
        check("/" in dlbl.cget("text"), "clock op set lblDate")
        # exercise move_by directly
        mv, _ = reloj.find_control("lblMove")
        x0 = int(mv.place_info().get("x", 0))
        actions.run_ops([{"op": "move_by", "target": "lblMove", "dx": 6,
                          "dy": 0, "wrap": True}], reloj.ctx)
        x1 = int(mv.place_info().get("x", 0))
        check(x1 == x0 + 6, "move_by shifted lblMove")

        # 5) op coverage on Portada -----------------------------------------
        actions.run_ops([{"op": "set_prop", "target": "lblTitle",
                          "prop": "caption", "value": "CAMBIADO"}], portada.ctx)
        check(lbl.cget("text") == "CAMBIADO", "set_prop changed caption")
        tg, tgm = portada.find_control("lblToggle")
        actions.run_ops([{"op": "toggle_visible", "target": "lblToggle"}],
                        portada.ctx)
        check(tgm.get("_visible") is False, "toggle_visible hid label")
        actions.run_ops([{"op": "toggle_visible", "target": "lblToggle"}],
                        portada.ctx)
        check(tgm.get("_visible") is True, "toggle_visible showed label")
        actions.run_ops([{"op": "beep"}], portada.ctx)
        actions.run_ops([{"op": "open_url", "url": "https://x.test"}],
                        portada.ctx)
        check("https://x.test" in _FakeBrowser.opened, "open_url called browser")
        _FakeMsg.calls.clear()
        actions.run_ops([{"op": "msgbox", "text": "hi", "icon": "warning"}],
                        portada.ctx)
        check(_FakeMsg.calls and _FakeMsg.calls[-1][0] == "warn",
              "msgbox routed by icon")
        # save_text writes the source control's text
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        tmp.close()
        _save_target["path"] = tmp.name
        actions.run_ops([{"op": "save_text", "source": "Articulo.txtBody",
                          "suggest_name": "a.txt"}], art.ctx)
        with open(tmp.name, encoding="utf-8") as fh:
            saved = fh.read()
        os.unlink(tmp.name)
        check("ANARQUIA DIGITAL" in saved, "save_text wrote Text content")
        # unsupported op does not raise
        actions.run_ops([{"op": "unsupported", "code": "Foo()", "note": "x"}],
                        portada.ctx)
        actions.run_ops([{"op": "bogus_op_name"}], portada.ctx)

        # 6) Acerca: modal + msgbox on_load ---------------------------------
        _FakeMsg.calls.clear()
        acerca = sess.show_form("Acerca", modal=True)
        app.root.update()
        check(any(c[0] == "info" for c in _FakeMsg.calls),
              "Acerca on_load fired msgbox")
        try:
            acerca.top.grab_release()
        except Exception:
            pass

        # 7) closing behaviour ----------------------------------------------
        n_open = len(sess.open_forms)
        sess.close_form("Acerca")
        check("Acerca" not in sess.open_forms, "close_form removed Acerca")
        check(len(sess.open_forms) == n_open - 1, "one fewer open form")
        check(closed["n"] == 0, "launcher not restored while forms remain")

        # quit closes the rest and notifies once
        sess.quit_issue()
        app.root.update()
        check(len(sess.open_forms) == 0, "quit_issue closed all forms")
        check(closed["n"] == 1, "on_closed fired exactly once")

        # 7b) HiDPI scaling: build the same form at SCALE=2 -----------------
        # Everything on screen must double; design coordinates stay in the
        # manifest. Restore SCALE=1.0 afterwards so later tests are unaffected.
        theme.SCALE = 2.0
        try:
            sess2 = engine.IssueSession(app.root, issue["dir"],
                                        issue["manifest"])
            hidpi = sess2.show_form("Portada")
            app.root.update()
            app.root.update_idletasks()
            # Toplevel geometry doubles (client 400x320 -> 800x640)
            geo = hidpi.top.geometry().split("+")[0]
            check(geo == "800x640", f"SCALE=2 toplevel geometry doubled ({geo})")
            # a control's place kwargs are in real (scaled) pixels
            _w, meta = hidpi.find_control("cmdArticulo")
            place = meta.get("_place") or {}
            check(place.get("x") == 32 and place.get("y") == 316,
                  "SCALE=2 control place doubled (16,158 -> 32,316)")
            # the background PhotoImage is scaled 2x (400x320 -> 800x640)
            check(any(getattr(p, "width", lambda: 0)() == 800 and
                      p.height() == 640 for p in hidpi._images),
                  "SCALE=2 background PhotoImage doubled to 800x640")
            sess2.quit_issue()
            app.root.update()
        finally:
            theme.SCALE = 1.0

    # 8) no dangling Toplevels & clean stderr -------------------------------
    print("[hygiene]")
    app.root.update()
    tops = [w for w in app.root.winfo_children()
            if w.winfo_class() == "Toplevel" and w.winfo_exists()]
    check(len(tops) == 0, "no dangling Toplevel windows")

    err = stderr_buf.getvalue()
    bad_markers = ("Traceback", "unsupported control", "missing asset",
                   "could not", "action error")
    offending = [ln for ln in err.splitlines()
                 if any(m in ln for m in bad_markers)]
    if offending:
        print("  --- unexpected stderr ---")
        for ln in offending:
            print("   ", ln)
    check(not offending, "no unexpected errors on stderr")
    # the expected 'unsupported action' log (Articulo on_load) may appear:
    check("unsupported action" in err, "expected unsupported-action log present")

    app.root.destroy()

    # -----------------------------------------------------------------------
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
