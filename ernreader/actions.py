"""Interpreter for behavior.json declarative actions.

Every op is executed inside a guard so imperfect data never raises out of an
event handler. Unknown ops (and the explicit ``unsupported`` op) log to stderr
and continue.
"""

from __future__ import annotations

import sys
import time
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox


def log(msg: str) -> None:
    print(f"[ernreader] {msg}", file=sys.stderr)


class ActionContext:
    """Bundle of references an op may need.

    Provided by the engine when wiring an event. ``form`` is the FormWindow the
    event fired on; ``session`` owns the collection of open forms for one issue.
    """

    def __init__(self, session, form, root):
        self.session = session
        self.form = form
        self.root = root

    # -- target resolution ---------------------------------------------------
    def resolve(self, target: str | None):
        """Resolve "Form.Control" | "Control" | "Form" to (form, widget, meta).

        A bare name is looked up first as a control on the current form, then as
        a form. Returns (form_or_None, widget_or_None, meta_or_None).
        """
        if not target:
            return self.form, None, None
        parts = target.split(".")
        if len(parts) == 2:
            form_name, ctrl_name = parts
            form = self.session.get_open_form(form_name) or self.form
            w, meta = form.find_control(ctrl_name) if form else (None, None)
            return form, w, meta
        name = parts[0]
        # try control on current form
        if self.form:
            w, meta = self.form.find_control(name)
            if w is not None:
                return self.form, w, meta
        # try a form by that name
        form = self.session.get_open_form(name)
        if form is not None:
            return form, None, None
        return self.form, None, None


def run_ops(ops, ctx: ActionContext) -> None:
    if not ops:
        return
    for op in ops:
        try:
            _dispatch(op, ctx)
        except Exception as exc:  # never let bad data break the UI
            log(f"action error in {op!r}: {exc}")


def _dispatch(op: dict, ctx: ActionContext) -> None:
    name = (op or {}).get("op")
    handler = _OPS.get(name)
    if handler is None:
        log(f"unknown op {name!r}: {op}")
        return
    handler(op, ctx)


# --- individual ops ----------------------------------------------------------

def _op_show_form(op, ctx):
    ctx.session.show_form(op.get("form"), modal=bool(op.get("modal")))


def _op_close(op, ctx):
    name = op.get("form")
    if not name and ctx.form is not None:
        name = ctx.form.name
    ctx.session.close_form(name)


def _op_quit(op, ctx):
    ctx.session.quit_issue()


def _op_save_text(op, ctx):
    _, widget, meta = ctx.resolve(op.get("source"))
    text = ""
    if widget is not None:
        text = _get_widget_text(widget)
    suggested = op.get("suggest_name") or "texto.txt"
    path = filedialog.asksaveasfilename(
        parent=ctx.form.top if ctx.form else None,
        initialfile=suggested,
        defaultextension=".txt",
        filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
    )
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError as exc:
        log(f"save_text failed: {exc}")


def _op_set_prop(op, ctx):
    _, widget, meta = ctx.resolve(op.get("target"))
    if widget is None:
        log(f"set_prop: target {op.get('target')!r} not found")
        return
    prop = (op.get("prop") or "").lower()
    value = op.get("value")
    _apply_prop(widget, meta, prop, value, ctx)


def _op_msgbox(op, ctx):
    icon = (op.get("icon") or "info").lower()
    title = op.get("title") or "El Radiaktivo Newz"
    text = op.get("text") or ""
    parent = ctx.form.top if ctx.form else None
    if icon in ("error", "critical", "stop"):
        messagebox.showerror(title, text, parent=parent)
    elif icon in ("warning", "exclamation"):
        messagebox.showwarning(title, text, parent=parent)
    else:
        messagebox.showinfo(title, text, parent=parent)


def _op_clock(op, ctx):
    _, widget, meta = ctx.resolve(op.get("target"))
    if widget is None:
        return
    what = (op.get("what") or "time").lower()
    if what == "date":
        value = time.strftime("%d/%m/%Y")
    else:
        value = time.strftime("%H:%M:%S")
    _set_text_like(widget, value)


def _op_move_by(op, ctx):
    _, widget, meta = ctx.resolve(op.get("target"))
    if widget is None:
        return
    dx = int(op.get("dx", 0) or 0)
    dy = int(op.get("dy", 0) or 0)
    try:
        x = int(widget.place_info().get("x", widget.winfo_x()))
        y = int(widget.place_info().get("y", widget.winfo_y()))
    except (tk.TclError, ValueError):
        x, y = widget.winfo_x(), widget.winfo_y()
    nx, ny = x + dx, y + dy
    if op.get("wrap"):
        parent = widget.master
        pw = parent.winfo_width() or 1
        ph = parent.winfo_height() or 1
        if nx > pw:
            nx = -widget.winfo_width()
        if ny > ph:
            ny = -widget.winfo_height()
        if nx < -widget.winfo_width():
            nx = pw
        if ny < -widget.winfo_height():
            ny = ph
    widget.place_configure(x=nx, y=ny)


def _op_open_url(op, ctx):
    url = op.get("url")
    if not url:
        return
    try:
        webbrowser.open(url)
    except Exception as exc:
        log(f"open_url failed: {exc}")


def _op_beep(op, ctx):
    try:
        (ctx.root or ctx.form.top).bell()
    except Exception:
        pass


def _op_toggle_visible(op, ctx):
    _, widget, meta = ctx.resolve(op.get("target"))
    if widget is None:
        return
    shown = meta.get("_visible", True) if meta else True
    _set_visible(widget, meta, not shown)


def _op_sequence(op, ctx):
    run_ops(op.get("ops", []), ctx)


def _op_if_text(op, ctx):
    """Conditional on a text control's contents (VB: If Text1.Text = "x")."""
    _, widget, _ = ctx.resolve(op.get("target"))
    if widget is None:
        run_ops(op.get("else", []), ctx)
        return
    current = _get_widget_text(widget)
    if current.endswith("\n"):  # tk.Text always appends one
        current = current[:-1]
    expected = op.get("equals") or ""
    # VB defaults to Option Compare Binary (case-sensitive)
    matched = current == expected if op.get("case_sensitive", True) \
        else current.lower() == expected.lower()
    run_ops(op.get("then", []) if matched else op.get("else", []), ctx)


def _op_gradient(op, ctx):
    """256-band linear gradient on a form's base canvas, as the original drew
    with Line/RGB loops. Redraws itself when the canvas resizes."""
    form = ctx.form
    target = op.get("target")
    if target:
        resolved, _, _ = ctx.resolve(target)
        if resolved is not None:
            form = resolved
    canvas = getattr(form, "base_canvas", None)
    if canvas is None:
        return
    c_from = _parse_hex(op.get("from") or "#040000")
    c_to = _parse_hex(op.get("to") or "#0400FF")

    def redraw(event=None):
        try:
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            canvas.delete("gradient")
            band = max(h / 256.0, 1.0)
            for i in range(256):
                rgb = tuple(int(a + (b - a) * i / 255) for a, b in zip(c_from, c_to))
                y = int(i * h / 256)
                canvas.create_rectangle(
                    0, y, w, int(y + band) + 1,
                    fill="#%02x%02x%02x" % rgb, outline="", tags="gradient")
            canvas.tag_lower("gradient")
        except tk.TclError:
            pass

    redraw()
    canvas.bind("<Configure>", redraw)


def _op_unsupported(op, ctx):
    note = op.get("note") or ""
    code = op.get("code") or ""
    log(f"unsupported action ({note}): {code!r}")


_OPS = {
    "show_form": _op_show_form,
    "close": _op_close,
    "quit": _op_quit,
    "save_text": _op_save_text,
    "set_prop": _op_set_prop,
    "msgbox": _op_msgbox,
    "clock": _op_clock,
    "move_by": _op_move_by,
    "open_url": _op_open_url,
    "beep": _op_beep,
    "toggle_visible": _op_toggle_visible,
    "sequence": _op_sequence,
    "if_text": _op_if_text,
    "gradient": _op_gradient,
    "unsupported": _op_unsupported,
}


def _parse_hex(color: str):
    color = (color or "").lstrip("#")
    try:
        return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (0, 0, 0)


# --- widget helpers ----------------------------------------------------------

def _get_widget_text(widget) -> str:
    if isinstance(widget, tk.Text):
        return widget.get("1.0", "end-1c")
    if isinstance(widget, tk.Entry):
        return widget.get()
    try:
        return widget.cget("text")
    except tk.TclError:
        return ""


def _set_text_like(widget, value: str) -> None:
    if isinstance(widget, tk.Text):
        state = str(widget.cget("state"))
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        if state == "disabled":
            widget.config(state="disabled")
    elif isinstance(widget, tk.Entry):
        widget.delete(0, "end")
        widget.insert(0, value)
    else:
        try:
            widget.config(text=value)
        except tk.TclError:
            pass


def _set_visible(widget, meta, visible: bool) -> None:
    if visible:
        info = meta.get("_place") if meta else None
        if info:
            widget.place(**info)
        else:
            try:
                widget.place_configure()
            except tk.TclError:
                pass
    else:
        widget.place_forget()
    if meta is not None:
        meta["_visible"] = visible


def _apply_prop(widget, meta, prop, value, ctx) -> None:
    if prop in ("caption", "text"):
        _set_text_like(widget, "" if value is None else str(value))
    elif prop == "visible":
        _set_visible(widget, meta, bool(value))
    elif prop == "enabled":
        try:
            widget.config(state="normal" if value else "disabled")
        except tk.TclError:
            pass
    elif prop in ("fore_color", "forecolor"):
        try:
            widget.config(fg=value)
        except tk.TclError:
            pass
    elif prop in ("back_color", "backcolor"):
        try:
            widget.config(bg=value)
        except tk.TclError:
            pass
    elif prop == "left":
        widget.place_configure(x=int(value))
    elif prop == "top":
        widget.place_configure(y=int(value))
    else:
        log(f"set_prop: unsupported prop {prop!r}")
