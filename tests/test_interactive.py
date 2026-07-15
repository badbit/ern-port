#!/usr/bin/env python3
"""End-to-end interactive run: exercises the *real* wired handlers (button and
menu commands, easter eggs, Extraer-to-file, search-to-open), not just
rendering. This is the regression guard for the whole user flow.

Modal dialogs (messagebox, filedialog) are stubbed so they capture instead of
blocking. Session state is redirected to a temp dir so the user's real
~/.local/share/ernreader/state.json is never touched. Needs a DISPLAY; skips
cleanly (exit 0) if Tk cannot start, same as the other GUI tests.

Run:  python3 tests/test_interactive.py
"""

import os
import sys
import time
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

DATA_DIR = os.path.join(ROOT, "data")

# Redirect session state away from the real user dir BEFORE importing state.
os.environ["XDG_DATA_HOME"] = tempfile.mkdtemp(prefix="ern_test_state_")

import tkinter as tk                                  # noqa: E402
from tkinter import filedialog, messagebox           # noqa: E402


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


# --- stub the modal dialogs so they capture instead of blocking --------------
_msgbox_calls = []
for _fn in ("showinfo", "showwarning", "showerror"):
    setattr(messagebox, _fn,
            lambda title=None, message=None, *a, **k:
            _msgbox_calls.append((title, message)))

_SAVE_PATH = os.path.join(os.environ["XDG_DATA_HOME"], "extraido.txt")
filedialog.asksaveasfilename = lambda *a, **k: _SAVE_PATH


def _pump(app, n=8):
    for _ in range(n):
        app.root.update()
        time.sleep(0.02)


def _issue(app, issue_id):
    return app.issues[[i["id"] for i in app.issues].index(issue_id)]


def _set_text(widget, val):
    try:
        widget.delete(0, "end")
        widget.insert(0, val)
    except tk.TclError:
        widget.delete("1.0", "end")
        widget.insert("1.0", val)


def run():
    from ernreader.launcher import Launcher
    from ernreader import search, state

    # [1] launcher discovers every issue
    print("[1] launcher")
    app = Launcher(DATA_DIR, scale="1", restore=False)
    _pump(app)
    check(len(app.issues) == 11, f"discovers 11 issues (found {len(app.issues)})")

    # [2] open an issue and navigate to an article
    print("[2] open issue + navigate")
    app.open_issue(_issue(app, "ERNSC2-5"))
    _pump(app)
    sess = app.session
    check(sess is not None and len(sess.open_forms) >= 1, "startup form opened")
    sess.show_form("anarquia")
    _pump(app)
    check("anarquia" in sess.open_forms, "article 'anarquia' opened")
    fw = sess.get_open_form("anarquia")

    # [3] Extraer article to a real .txt file
    print("[3] Extraer -> file")
    extract_key = next(
        (k for k, ops in fw._events.items()
         if any(o.get("op") == "save_text" for o in ops)), None)
    if extract_key:
        fw._fire(fw._events[extract_key])
        _pump(app)
    check(os.path.exists(_SAVE_PATH), f"'Extraer' wrote the file ({extract_key})")
    if os.path.exists(_SAVE_PATH):
        content = open(_SAVE_PATH, encoding="utf-8", errors="replace").read()
        check(len(content) > 500, f"extracted .txt has article content "
                                  f"({len(content)} chars)")

    # [4] password easter egg (Acerca of ERNSC1-5)
    print("[4] easter egg")
    app.session.quit_issue()
    _pump(app)
    app.open_issue(_issue(app, "ERNSC1-5"))
    _pump(app)
    s5 = app.session
    s5.show_form("Acerca")
    _pump(app)
    acer = s5.get_open_form("Acerca")
    ev = acer._events.get("Command1.Click")
    w, _meta = acer.find_control("Text1")

    # wrong password first (window stays open, nothing revealed)
    _set_text(w, "xxx")
    _msgbox_calls.clear()
    if ev:
        acer._fire(ev)
        _pump(app)
    check(len(_msgbox_calls) == 0, "wrong password reveals nothing")
    check("Acerca" in s5.open_forms, "wrong password keeps the window open")

    # correct password reveals the secret and closes the window (VB behaviour)
    _set_text(w, "Aquamosh")
    _msgbox_calls.clear()
    if ev:
        acer._fire(ev)
        _pump(app)
    check(any("3E FF 98 A0" in str(m[1]) for m in _msgbox_calls),
          "correct password fires the secret MsgBox")
    check("Acerca" not in s5.open_forms, "revealing the secret closes Acerca")

    # [5] quit back to launcher
    print("[5] quit -> launcher")
    app.session.quit_issue()
    _pump(app)
    check(app.session is None or not app.session.open_forms,
          "issue windows closed")

    # [6] search then open a result
    print("[6] search -> open result")
    idx = search.SearchIndex(DATA_DIR)
    res = idx.search("telnor")
    check(len(res) >= 1, f"'telnor' finds result(s) ({len(res)})")
    check(len(idx.search("pedo historia")) >= 1,
          "'pedo historia' (AND) finds the article")
    if res:
        r = res[0]
        app.open_issue_form(r.issue_id, r.form_name)
        _pump(app)
        check(app.session is not None and r.form_name in app.session.open_forms,
              f"opening a result shows {r.issue_id}/{r.form_name}")
        app.session.quit_issue()
        _pump(app)

    # [7] maximized forms grow to content; reader textbox follows resizes
    print("[7] maximized + resize")
    app.open_issue(_issue(app, "ERNSC1-1"))
    _pump(app)
    s1 = app.session
    s1.show_form("Form4")   # WindowState=2: design 385x302, content 617x425
    _pump(app)
    f4 = s1.get_open_form("Form4")
    check(f4.top.winfo_width() >= 617 and f4.top.winfo_height() >= 425,
          f"maximized Form4 grew to its content "
          f"({f4.top.winfo_width()}x{f4.top.winfo_height()})")
    s1.quit_issue()
    _pump(app)

    app.open_issue(_issue(app, "ERNSC2-5"))
    _pump(app)
    s25 = app.session
    s25.show_form("anarquia")
    _pump(app)
    fa = s25.get_open_form("anarquia")
    txt, meta = fa.find_control("txtEdit")
    outer = meta.get("_outer") or txt
    w0 = outer.winfo_width()
    check(abs(w0 - fa.top.winfo_width()) <= 4,
          f"reader textbox fills the window on open ({w0})")
    fa.top.geometry(f"{fa.top.winfo_width() + 150}"
                    f"x{fa.top.winfo_height() + 100}")
    _pump(app, 20)
    check(outer.winfo_width() >= w0 + 140,
          f"reader textbox follows window resize ({outer.winfo_width()})")
    s25.quit_issue()
    _pump(app)

    # [8] session state persisted
    print("[8] session state")
    st = state.load_state()
    check(st.get("last_issue") is not None,
          f"last read issue saved ({st.get('last_issue')})")

    app.root.destroy()


def main():
    try:
        tk.Tk().destroy()
    except tk.TclError as exc:
        print(f"[skip] no DISPLAY / Tk unavailable: {exc}")
        return 0
    run()
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
