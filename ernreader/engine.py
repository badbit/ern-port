"""Tkinter rendering engine: manifest.json form -> tk.Toplevel.

One :class:`IssueSession` owns all open forms of a single issue and the shared
behavior.json. Each :class:`FormWindow` renders one form with pixel-exact
``place`` geometry, matching the original VB layout as closely as Tk allows.
"""

from __future__ import annotations

import os
import re
import sys
import json
import tkinter as tk

try:
    from PIL import Image, ImageTk
    _HAVE_PIL = True
except Exception:  # pragma: no cover - Pillow is a declared dependency
    _HAVE_PIL = False

from . import theme
from .actions import ActionContext, run_ops, log


# Border styles that allow resizing (2 Sizable, 5 Sizable ToolWindow).
_RESIZABLE_BORDERS = {2, 5}


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        log(f"could not read {path}: {exc}")
        return None


class IssueSession:
    """Manages the open forms of one issue and returns to the launcher."""

    def __init__(self, root, issue_dir, manifest, on_closed=None):
        self.root = root
        self.issue_dir = issue_dir
        self.manifest = manifest
        self.on_closed = on_closed
        self.behavior = load_json(os.path.join(issue_dir, "behavior.json")) or {}
        if not self.behavior:
            log(f"no behavior.json for {manifest.get('issue_id')}; "
                "rendering without actions")
        self.forms = manifest.get("forms", {})
        self.open_forms: dict[str, FormWindow] = {}
        self._closing = False

    # -- lifecycle -----------------------------------------------------------
    def start(self):
        startup = self.manifest.get("startup_form")
        order = self.manifest.get("form_order") or list(self.forms.keys())
        if not startup or startup not in self.forms:
            startup = order[0] if order else None
        if not startup:
            log("issue has no forms to show")
            self._notify_closed()
            return
        self.show_form(startup)

    def show_form(self, name, modal=False):
        if not name or name not in self.forms:
            log(f"show_form: unknown form {name!r}")
            return None
        existing = self.open_forms.get(name)
        if existing is not None:
            existing.top.deiconify()
            existing.top.lift()
            return existing
        fw = FormWindow(self, name, self.forms[name])
        self.open_forms[name] = fw
        fw.build()
        if modal:
            try:
                fw.top.transient(self.root)
                fw.top.grab_set()
            except tk.TclError:
                pass
        return fw

    def close_form(self, name):
        fw = self.open_forms.get(name)
        if fw is None:
            return
        del self.open_forms[name]
        fw.destroy()
        if not self.open_forms and not self._closing:
            self._notify_closed()

    def quit_issue(self):
        self._closing = True
        for fw in list(self.open_forms.values()):
            fw.destroy()
        self.open_forms.clear()
        self._closing = False
        self._notify_closed()

    def _notify_closed(self):
        if self.on_closed:
            self.on_closed(self)

    def get_open_form(self, name):
        return self.open_forms.get(name)

    def behavior_for(self, form_name):
        return (self.behavior.get("forms", {}) or {}).get(form_name, {})


class FormWindow:
    """Renders a single form dict into a tk.Toplevel."""

    def __init__(self, session: IssueSession, name: str, form: dict):
        self.session = session
        self.name = name
        self.form = form
        self.top = tk.Toplevel(session.root)
        self.controls: dict[str, tuple] = {}     # name -> (widget, meta)
        self._images = []                        # keep PhotoImage refs alive
        self._timers = []                        # after() ids
        self._behavior = session.behavior_for(name)
        self._events = self._behavior.get("events", {}) or {}
        self.ctx = ActionContext(session, self, session.root)

    # -- helpers -------------------------------------------------------------
    def find_control(self, name):
        return self.controls.get(name, (None, None))

    def _asset(self, rel):
        if not rel:
            return None
        path = os.path.join(self.session.issue_dir, rel)
        if not os.path.exists(path):
            log(f"missing asset: {rel}")
            return None
        if not _HAVE_PIL:
            return None
        try:
            return Image.open(path)
        except Exception as exc:
            log(f"could not load image {rel}: {exc}")
            return None

    def _photo(self, rel, size=None):
        img = self._asset(rel)
        if img is None:
            return None
        try:
            if size:
                img = img.resize(size)
            photo = ImageTk.PhotoImage(img)
            self._images.append(photo)
            return photo
        except Exception as exc:
            log(f"could not convert image {rel}: {exc}")
            return None

    def _events_for(self, ctrl_name, event="Click"):
        return self._events.get(f"{ctrl_name}.{event}")

    def _fire(self, ops):
        run_ops(ops, self.ctx)

    # -- build ---------------------------------------------------------------
    def build(self):
        f = self.form
        w = int(f.get("client_w") or 320)
        h = int(f.get("client_h") or 240)
        self.top.title(f.get("caption") or self.name)
        # VB forms centered themselves on load (Top/Left = Screen.Height/2 -
        # Height/2 boilerplate); make that the default placement.
        sx = max((self.top.winfo_screenwidth() - w) // 2, 0)
        sy = max((self.top.winfo_screenheight() - h) // 2 - 20, 0)
        self.top.geometry(f"{w}x{h}+{sx}+{sy}")
        self.top.minsize(1, 1)
        border = f.get("border_style")
        resizable = border in _RESIZABLE_BORDERS
        self.top.resizable(resizable, resizable)
        back_color = f.get("back_color") or theme.BUTTON_FACE
        self.top.configure(bg=back_color)

        # window icon
        icon_photo = self._photo(f.get("icon"))
        if icon_photo is not None:
            try:
                self.top.iconphoto(False, icon_photo)
            except tk.TclError:
                pass

        # base canvas = background + shapes layer
        self.base_canvas = tk.Canvas(self.top, width=w, height=h,
                                     highlightthickness=0, bd=0, bg=back_color)
        self.base_canvas.place(x=0, y=0, width=w, height=h)
        pic = self._photo(f.get("picture"))
        if pic is not None:
            self.base_canvas.create_image(0, 0, anchor="nw", image=pic)
        # keep a PIL copy of the background clipped to the client area, so
        # transparent (BackStyle=0) controls can sample the pixels behind them
        self._bg_pil = None
        if _HAVE_PIL and f.get("picture"):
            src = self._asset(f.get("picture"))
            if src is not None:
                try:
                    self._bg_pil = src.convert("RGB").crop((0, 0, w, h))
                except Exception:
                    self._bg_pil = None

        # controls (z-order = order in list)
        self._render_controls(self.top, f.get("controls", []), self.base_canvas)

        # menu
        if f.get("menu"):
            self._build_menu(f["menu"])

        # article readers resized their big TextBox to fill the form
        # (txtEdit.Width = ScaleWidth boilerplate); replicate for resizable
        # forms on any near-full-size multiline TextBox.
        if resizable:
            self._wire_autofill(w, h)

        # window close protocol -> behaves like closing this form
        self.top.protocol("WM_DELETE_WINDOW", self._on_wm_close)

        # on_load actions
        on_load = self._behavior.get("on_load")
        if on_load:
            self.top.after(0, lambda: self._fire(on_load))

    def _wire_autofill(self, client_w, client_h):
        candidates = []
        for _name, (widget, meta) in self.controls.items():
            pl = meta.get("_place") or {}
            if (meta.get("type") == "TextBox" and widget is not None
                    and widget.master is self.top
                    and pl.get("width", 0) >= 0.7 * client_w
                    and pl.get("height", 0) >= 0.7 * client_h):
                candidates.append((widget, pl))
        if not candidates:
            return

        def on_configure(event):
            if event.widget is not self.top:
                return
            for widget, pl in candidates:
                try:
                    widget.place_configure(
                        width=max(event.width - pl.get("x", 0), 10),
                        height=max(event.height - pl.get("y", 0), 10))
                except tk.TclError:
                    pass

        self.top.bind("<Configure>", on_configure, add="+")

    def _on_wm_close(self):
        # closing a window == closing that form; session handles returning to
        # the launcher when the last one goes.
        self.session.close_form(self.name)

    # -- control rendering ---------------------------------------------------
    def _render_controls(self, parent, controls, canvas):
        for ctrl in controls or []:
            try:
                self._build_control(parent, ctrl, canvas)
            except Exception as exc:
                log(f"failed to build control {ctrl.get('name')!r}: {exc}")

    def _build_control(self, parent, ctrl, canvas):
        ctype = ctrl.get("type")
        builder = _BUILDERS.get(ctype)
        if builder is None:
            log(f"unsupported control type {ctype!r} ({ctrl.get('name')}); "
                "rendering placeholder")
            builder = _build_placeholder
        builder(self, parent, ctrl, canvas)

    def _register(self, ctrl, widget, place_kwargs):
        meta = {
            "type": ctrl.get("type"),
            "_visible": _flag(ctrl, "visible"),
            "_place": dict(place_kwargs) if place_kwargs else None,
        }
        name = ctrl.get("name")
        if name:
            self.controls[name] = (widget, meta)
        if not _flag(ctrl, "visible") and widget is not None:
            widget.place_forget()
        return meta

    def _wire_click(self, widget, ctrl, kind="command"):
        ops = self._events_for(ctrl.get("name"), "Click")
        if not ops:
            return
        if kind == "command":
            widget.config(command=lambda o=ops: self._fire(o))
        else:
            widget.bind("<Button-1>", lambda e, o=ops: self._fire(o))

    # -- menu ----------------------------------------------------------------
    def _build_menu(self, menu_list):
        menubar = tk.Menu(self.top, tearoff=0)
        for item in menu_list:
            self._add_menu_item(menubar, item, top_level=True)
        try:
            self.top.config(menu=menubar)
        except tk.TclError as exc:
            log(f"could not attach menu: {exc}")

    def _add_menu_item(self, parent_menu, item, top_level=False):
        caption = item.get("caption", "")
        children = item.get("children") or []
        label, underline = _parse_amp(caption)
        if caption == "-":
            parent_menu.add_separator()
            return
        if children:
            submenu = tk.Menu(parent_menu, tearoff=0)
            for child in children:
                self._add_menu_item(submenu, child)
            parent_menu.add_cascade(label=label, underline=underline,
                                    menu=submenu)
        else:
            ops = self._events_for(item.get("name"), "Click")
            accel, binding = _parse_shortcut(item.get("shortcut"))
            parent_menu.add_command(
                label=label, underline=underline, accelerator=accel,
                command=(lambda o=ops: self._fire(o)) if ops else _noop,
            )
            if binding and ops:
                self.top.bind(binding, lambda e, o=ops: self._fire(o))

    # -- destruction ---------------------------------------------------------
    def destroy(self):
        for tid in self._timers:
            try:
                self.top.after_cancel(tid)
            except Exception:
                pass
        self._timers.clear()
        self._images.clear()
        self.controls.clear()
        try:
            self.top.destroy()
        except tk.TclError:
            pass


# --- control builders --------------------------------------------------------
# Each takes (FormWindow self, parent widget, ctrl dict, base canvas).

def _flag(ctrl, key, default=True):
    """VB omits properties left at their default, so the manifest carries
    null; only an explicit false means false."""
    val = ctrl.get(key)
    return default if val is None else bool(val)


def _place_kwargs(ctrl):
    kw = {"x": int(ctrl.get("x", 0) or 0), "y": int(ctrl.get("y", 0) or 0)}
    if ctrl.get("w"):
        kw["width"] = int(ctrl["w"])
    if ctrl.get("h"):
        kw["height"] = int(ctrl["h"])
    return kw


def _control_text(fw: FormWindow, ctrl):
    """Return inline text/caption or the contents of text_file."""
    if ctrl.get("text_file"):
        path = os.path.join(fw.session.issue_dir, ctrl["text_file"])
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except OSError as exc:
            log(f"missing text file {ctrl['text_file']}: {exc}")
            return ""
    val = ctrl.get("text")
    if val is None:
        val = ctrl.get("caption")
    return val or ""


def _bg_for(fw: FormWindow, ctrl, parent, default):
    """Approximate BackStyle=0 (transparent). When the form has a background
    picture, sample the pixels the control sits over so it blends in; otherwise
    inherit the parent bg color."""
    if ctrl.get("back_style") == 0:
        sampled = _sample_bg(fw, ctrl)
        if sampled:
            return sampled
        try:
            return parent.cget("bg")
        except tk.TclError:
            return default
    return ctrl.get("back_color") or default


def _sample_bg(fw, ctrl):
    """Average color of the background picture under a control's rect, as hex,
    or None if there is no picture / the region is not uniform enough."""
    pil = getattr(fw, "_bg_pil", None)
    if pil is None or parent_is_nested(ctrl):
        return None
    try:
        x = int(ctrl.get("x", 0) or 0)
        y = int(ctrl.get("y", 0) or 0)
        w = max(int(ctrl.get("w", 1) or 1), 1)
        h = max(int(ctrl.get("h", 1) or 1), 1)
        box = (max(x, 0), max(y, 0),
               min(x + w, pil.width), min(y + h, pil.height))
        if box[2] <= box[0] or box[3] <= box[1]:
            return None
        region = pil.crop(box)
        # extrema per channel; if the region is roughly uniform, use its
        # average — otherwise sampling would smear text over detailed art.
        ex = region.getextrema()
        if max(hi - lo for lo, hi in ex) > 60:
            return None
        px = region.resize((1, 1))
        r, g, b = px.getpixel((0, 0))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return None


def parent_is_nested(ctrl):
    return False


def _build_button(fw, parent, ctrl, canvas):
    kw = _place_kwargs(ctrl)
    photo = fw._photo(ctrl.get("picture")) if ctrl.get("picture") else None
    label, underline = _parse_amp(ctrl.get("caption") or "")
    btn = tk.Button(
        parent, text=label, underline=underline,
        font=theme.resolve_font(ctrl.get("font")),
        fg=ctrl.get("fore_color") or theme.BUTTON_TEXT,
        bg=ctrl.get("back_color") or theme.BUTTON_FACE,
        activebackground=theme.BUTTON_FACE,
        relief="raised", bd=2, highlightthickness=1,
        takefocus=1,
    )
    if photo is not None:
        btn.config(image=photo, compound="center")
    # VB wraps long button captions within the control width
    if ctrl.get("w") and int(ctrl["w"]) > 12:
        btn.config(wraplength=int(ctrl["w"]) - 12)
    if not _flag(ctrl, "enabled"):
        btn.config(state="disabled")
    btn.place(**kw)
    fw._register(ctrl, btn, kw)
    fw._wire_click(btn, ctrl, "command")


def _build_label(fw, parent, ctrl, canvas):
    kw = _place_kwargs(ctrl)
    align = ctrl.get("alignment") or 0
    anchor = {0: "nw", 1: "ne", 2: "n"}.get(align, "nw")
    justify = {0: "left", 1: "right", 2: "center"}.get(align, "left")
    lbl = tk.Label(
        parent, text=_control_text(fw, ctrl),
        font=theme.resolve_font(ctrl.get("font")),
        fg=ctrl.get("fore_color") or theme.WINDOW_TEXT,
        bg=_bg_for(fw, ctrl, parent, theme.BUTTON_FACE),
        anchor=anchor, justify=justify,
        bd=(1 if ctrl.get("border_style") else 0),
        relief=("solid" if ctrl.get("border_style") else "flat"),
    )
    # VB labels always wrap at the control width (WordWrap only affects
    # vertical autosizing), except when AutoSize grows them horizontally.
    if ctrl.get("w") and not (ctrl.get("auto_size") and not ctrl.get("word_wrap")):
        lbl.config(wraplength=int(ctrl["w"]))
    if not _flag(ctrl, "enabled"):
        lbl.config(state="disabled")
    lbl.place(**kw)
    fw._register(ctrl, lbl, kw)
    fw._wire_click(lbl, ctrl, "bind")


def _build_textbox(fw, parent, ctrl, canvas):
    kw = _place_kwargs(ctrl)
    font = theme.resolve_font(ctrl.get("font"))
    fg = ctrl.get("fore_color") or theme.WINDOW_TEXT
    bg = ctrl.get("back_color") or theme.WINDOW
    if not ctrl.get("multiline"):
        entry = tk.Entry(parent, font=font, fg=fg, bg=bg,
                         relief="sunken", bd=2)
        entry.insert(0, _control_text(fw, ctrl))
        if ctrl.get("locked"):
            entry.config(state="readonly")
        if not _flag(ctrl, "enabled"):
            entry.config(state="disabled")
        entry.place(**kw)
        fw._register(ctrl, entry, kw)
        return

    # multiline -> Text + scrollbars inside a placed frame
    holder = tk.Frame(parent, bd=2, relief="sunken", bg=bg)
    holder.place(**kw)
    scrollbars = ctrl.get("scrollbars") or 0
    text = tk.Text(holder, font=font, fg=fg, bg=bg,
                   wrap=("word" if ctrl.get("word_wrap") else "none"),
                   bd=0, highlightthickness=0,
                   insertbackground=fg)
    if scrollbars in (2, 3):
        vsb = tk.Scrollbar(holder, orient="vertical", command=text.yview)
        vsb.pack(side="right", fill="y")
        text.config(yscrollcommand=vsb.set)
    if scrollbars in (1, 3):
        hsb = tk.Scrollbar(holder, orient="horizontal", command=text.xview)
        hsb.pack(side="bottom", fill="x")
        text.config(xscrollcommand=hsb.set, wrap="none")
    text.pack(side="left", fill="both", expand=True)
    text.insert("1.0", _control_text(fw, ctrl))
    if ctrl.get("locked"):
        text.config(state="disabled")
    # register the Text widget itself (so save_text/set_prop reach it)
    fw._register(ctrl, text, kw)


def _build_image(fw, parent, ctrl, canvas):
    kw = _place_kwargs(ctrl)
    size = None
    if ctrl.get("stretch") and ctrl.get("w") and ctrl.get("h"):
        size = (int(ctrl["w"]), int(ctrl["h"]))
    photo = fw._photo(ctrl.get("picture"), size=size) if ctrl.get("picture") else None
    lbl = tk.Label(parent, image=photo, bd=0,
                   bg=_bg_for(fw, ctrl, parent, theme.BUTTON_FACE))
    if photo is None:
        lbl.config(text=ctrl.get("caption") or "", compound="center")
    lbl.place(**kw)
    fw._register(ctrl, lbl, kw)
    fw._wire_click(lbl, ctrl, "bind")


def _build_picturebox(fw, parent, ctrl, canvas):
    kw = _place_kwargs(ctrl)
    bg = ctrl.get("back_color") or theme.BUTTON_FACE
    children = ctrl.get("children") or []
    has_shapes = any(c.get("type") in ("Line", "Shape") for c in children)
    frame = tk.Frame(parent, bg=bg, bd=2, relief="sunken",
                     width=int(ctrl.get("w", 0) or 0),
                     height=int(ctrl.get("h", 0) or 0))
    frame.place(**kw)
    frame.pack_propagate(False)
    frame.grid_propagate(False)
    inner_canvas = canvas
    photo = fw._photo(ctrl.get("picture")) if ctrl.get("picture") else None
    if photo is not None or has_shapes:
        inner_canvas = tk.Canvas(frame, highlightthickness=0, bd=0, bg=bg,
                                 width=int(ctrl.get("w", 0) or 0),
                                 height=int(ctrl.get("h", 0) or 0))
        inner_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        if photo is not None:
            inner_canvas.create_image(0, 0, anchor="nw", image=photo)
    fw._register(ctrl, frame, kw)
    fw._render_controls(frame, children, inner_canvas)


def _build_frame(fw, parent, ctrl, canvas):
    kw = _place_kwargs(ctrl)
    lf = tk.LabelFrame(parent, text=ctrl.get("caption") or "",
                       font=theme.resolve_font(ctrl.get("font")),
                       fg=ctrl.get("fore_color") or theme.WINDOW_TEXT,
                       bg=ctrl.get("back_color") or theme.BUTTON_FACE)
    lf.place(**kw)
    children = ctrl.get("children") or []
    has_shapes = any(c.get("type") in ("Line", "Shape") for c in children)
    inner = canvas
    if has_shapes:
        inner = tk.Canvas(lf, highlightthickness=0, bd=0,
                          bg=ctrl.get("back_color") or theme.BUTTON_FACE)
        inner.place(x=0, y=0, relwidth=1, relheight=1)
    fw._register(ctrl, lf, kw)
    fw._render_controls(lf, children, inner)


def _build_timer(fw, parent, ctrl, canvas):
    interval = ctrl.get("interval")
    if not _flag(ctrl, "enabled") or not interval:
        # still register so set_prop(enabled) could reference it
        fw._register(ctrl, None, None)
        return
    ops = fw._events_for(ctrl.get("name"), "Timer")
    interval = int(interval)

    def loop():
        if ops:
            fw._fire(ops)
        tid = fw.top.after(interval, loop)
        fw._timers.append(tid)

    tid = fw.top.after(interval, loop)
    fw._timers.append(tid)
    fw._register(ctrl, None, None)


def _vb_color(value, default=None):
    """Convert a VB &H00BBGGRR& color literal to #RRGGBB. Already-hex passes
    through. Returns default on anything unparseable."""
    if not value:
        return default
    s = str(value).strip()
    if s.startswith("#"):
        return s
    m = re.match(r"&[Hh]([0-9A-Fa-f]{1,8})&?$", s)
    if not m:
        return default
    n = int(m.group(1), 16) & 0xFFFFFF
    b, g, r = (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF
    return f"#{r:02x}{g:02x}{b:02x}"


def _build_line(fw, parent, ctrl, canvas):
    raw = ctrl.get("raw") or {}
    try:
        x1 = int(float(raw.get("X1", raw.get("_x1", ctrl.get("x", 0)))))
        y1 = int(float(raw.get("Y1", raw.get("_y1", ctrl.get("y", 0)))))
        x2 = int(float(raw.get("X2", raw.get("_x2", ctrl.get("x", 0)))))
        y2 = int(float(raw.get("Y2", raw.get("_y2", ctrl.get("y", 0)))))
    except (TypeError, ValueError):
        return
    color = (ctrl.get("fore_color") or _vb_color(raw.get("BorderColor"))
             or "#000000")
    try:
        width = max(int(float(raw.get("BorderWidth", 1))), 1)
    except (TypeError, ValueError):
        width = 1
    if canvas is not None:
        canvas.create_line(x1, y1, x2, y2, fill=color, width=width)


# VB Shape property: 0 Rect, 1 Square, 2 Oval, 3 Circle, 4 RoundedRect,
# 5 RoundedSquare.
def _rounded_rect(canvas, x, y, w, h, r, **kw):
    r = max(0, min(r, w // 2, h // 2))
    x2, y2 = x + w, y + h
    pts = [x + r, y, x2 - r, y, x2, y, x2, y + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x + r, y2, x, y2, x, y2 - r, x, y + r, x, y]
    return canvas.create_polygon(pts, smooth=True, **kw)


def _build_shape(fw, parent, ctrl, canvas):
    if canvas is None:
        return
    x = int(ctrl.get("x", 0) or 0)
    y = int(ctrl.get("y", 0) or 0)
    w = int(ctrl.get("w", 0) or 0)
    h = int(ctrl.get("h", 0) or 0)
    raw = ctrl.get("raw") or {}
    shape = str(raw.get("Shape", raw.get("shape", "0")))
    outline = (ctrl.get("fore_color") or _vb_color(raw.get("BorderColor"))
               or "#000000")
    try:
        width = max(int(float(raw.get("BorderWidth", 1))), 1)
    except (TypeError, ValueError):
        width = 1
    fill = ""
    if ctrl.get("back_style") == 1 or str(raw.get("FillStyle")) == "0":
        fill = ctrl.get("back_color") or _vb_color(raw.get("FillColor")) or ""
    if shape in ("2", "3"):        # oval / circle
        canvas.create_oval(x, y, x + w, y + h, outline=outline, fill=fill,
                           width=width)
    elif shape in ("4", "5"):      # rounded rectangle / rounded square
        _rounded_rect(canvas, x, y, w, h, r=min(w, h) // 5 + 6,
                      outline=outline, fill=fill or "", width=width)
    else:                          # rectangle / square
        canvas.create_rectangle(x, y, x + w, y + h, outline=outline,
                                fill=fill, width=width)


def _build_checkbox(fw, parent, ctrl, canvas):
    kw = _place_kwargs(ctrl)
    var = tk.IntVar(value=1 if ctrl.get("value") else 0)
    _lbl, _und = _parse_amp(ctrl.get("caption") or "")
    cb = tk.Checkbutton(parent, text=_lbl, underline=_und, variable=var,
                        font=theme.resolve_font(ctrl.get("font")),
                        bg=_bg_for(fw, ctrl, parent, theme.BUTTON_FACE),
                        fg=ctrl.get("fore_color") or theme.WINDOW_TEXT,
                        activebackground=theme.BUTTON_FACE,
                        anchor="w", relief="flat", highlightthickness=0)
    cb._ern_var = var  # keep ref
    if not _flag(ctrl, "enabled"):
        cb.config(state="disabled")
    cb.place(**kw)
    fw._register(ctrl, cb, kw)
    fw._wire_click(cb, ctrl, "command")


def _build_option(fw, parent, ctrl, canvas):
    kw = _place_kwargs(ctrl)
    var = tk.StringVar(value=ctrl.get("name"))
    _lbl, _und = _parse_amp(ctrl.get("caption") or "")
    rb = tk.Radiobutton(parent, text=_lbl, underline=_und,
                        variable=var, value=ctrl.get("name"),
                        font=theme.resolve_font(ctrl.get("font")),
                        bg=_bg_for(fw, ctrl, parent, theme.BUTTON_FACE),
                        fg=ctrl.get("fore_color") or theme.WINDOW_TEXT,
                        activebackground=theme.BUTTON_FACE,
                        anchor="w", relief="flat", highlightthickness=0)
    rb._ern_var = var
    if not _flag(ctrl, "enabled"):
        rb.config(state="disabled")
    rb.place(**kw)
    fw._register(ctrl, rb, kw)
    fw._wire_click(rb, ctrl, "command")


def _build_listbox(fw, parent, ctrl, canvas):
    kw = _place_kwargs(ctrl)
    lb = tk.Listbox(parent, font=theme.resolve_font(ctrl.get("font")),
                    fg=ctrl.get("fore_color") or theme.WINDOW_TEXT,
                    bg=ctrl.get("back_color") or theme.WINDOW,
                    relief="sunken", bd=2, highlightthickness=0)
    lb.place(**kw)
    fw._register(ctrl, lb, kw)


def _build_placeholder(fw, parent, ctrl, canvas):
    """Unknown/unsupported control: visible marker, never crashes."""
    kw = _place_kwargs(ctrl)
    lbl = tk.Label(parent, text=f"[{ctrl.get('type')}]",
                   font=theme.ui_font(7), fg="#606060",
                   bg=_bg_for(fw, ctrl, parent, theme.BUTTON_FACE),
                   bd=1, relief="groove")
    lbl.place(**kw)
    fw._register(ctrl, lbl, kw)


_BUILDERS = {
    "CommandButton": _build_button,
    "Label": _build_label,
    "TextBox": _build_textbox,
    "Image": _build_image,
    "PictureBox": _build_picturebox,
    "Frame": _build_frame,
    "Timer": _build_timer,
    "Line": _build_line,
    "Shape": _build_shape,
    "CheckBox": _build_checkbox,
    "OptionButton": _build_option,
    "ListBox": _build_listbox,
    "ComboBox": _build_listbox,
}


# --- small parsing utilities -------------------------------------------------

def _noop():
    pass


def _parse_amp(caption):
    """VB '&X' accelerator -> (clean_label, underline_index or -1)."""
    if not caption:
        return "", -1
    out = []
    underline = -1
    i = 0
    while i < len(caption):
        ch = caption[i]
        if ch == "&" and i + 1 < len(caption):
            nxt = caption[i + 1]
            if nxt == "&":
                out.append("&")
                i += 2
                continue
            if underline == -1:
                underline = len(out)
            out.append(nxt)
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out), underline


# VB menu shortcut codes -> (accelerator label, tk binding)
_KEYNAMES = {
    "^": ("Ctrl", "Control"),
}


def _parse_shortcut(shortcut):
    """'^E' -> ('Ctrl+E', '<Control-e>'). Best-effort for common cases."""
    if not shortcut:
        return None, None
    s = shortcut.strip()
    mods_label = []
    mods_bind = []
    while s and s[0] in "^+%":
        if s[0] == "^":
            mods_label.append("Ctrl")
            mods_bind.append("Control")
        elif s[0] == "+":
            mods_label.append("Shift")
            mods_bind.append("Shift")
        elif s[0] == "%":
            mods_label.append("Alt")
            mods_bind.append("Alt")
        s = s[1:]
    key = s.strip()
    if not key:
        return None, None
    # function keys like {F1}
    if key.startswith("{") and key.endswith("}"):
        key = key[1:-1]
        bind_key = key
        label_key = key
    else:
        label_key = key.upper()
        bind_key = key.lower() if len(key) == 1 else key
    accel = "+".join(mods_label + [label_key])
    binding = "<" + "-".join(mods_bind + [bind_key]) + ">"
    return accel, binding
