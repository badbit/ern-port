"""The collection launcher: a classic Win95 window listing the issues.

Scans the data directory for ``<ISSUE>/manifest.json`` files, shows title and
date (parsed from ``version_comments``), and opens an issue's startup form when
chosen. Returning from an issue (last window closed, or ``quit``) re-shows it.
"""

from __future__ import annotations

import os
import re
import time
import tkinter as tk

from . import theme, search, state
from .engine import IssueSession, load_json, log


# Rough month table to normalize dates parsed from version_comments.
_MONTHS = ("enero febrero marzo abril mayo junio julio agosto septiembre "
           "octubre noviembre diciembre").split()


def parse_comments(text):
    """Split version_comments into (headline, date_str).

    Example: "El Radiactivo News, Agosto 1998. Número 1, Año I"
    -> ("El Radiactivo News", "Agosto 1998")
    """
    if not text:
        return "", ""
    date = ""
    m = re.search(r"([A-Za-zÁÉÍÓÚáéíóúñ]+)\s+(\d{4})", text)
    if m and m.group(1).lower() in _MONTHS:
        date = f"{m.group(1)} {m.group(2)}"
    elif m:
        date = f"{m.group(1)} {m.group(2)}"
    else:
        m2 = re.search(r"\b(19|20)\d{2}\b", text)
        if m2:
            date = m2.group(0)
    headline = text.split(",")[0].strip() if "," in text else text.strip()
    return headline, date


# The original version_comments have a few author typos in the date/number
# (e.g. ERNSC1-4 says "Número 3"). The folder id ERNSC<año>-<nº> is reliable, so
# we derive año/número from it and use it as the authoritative label.
_ROMAN = {1: "I", 2: "II"}


def issue_label(issue_id):
    """ERNSC1-3 -> ('Año I, Nº 3', (1, 3)); unknown -> (issue_id, (99, 99))."""
    m = re.match(r"ERNSC(\d+)-(\d+)", issue_id or "")
    if not m:
        return issue_id, (99, 99)
    year, num = int(m.group(1)), int(m.group(2))
    return f"Año {_ROMAN.get(year, year)}, Nº {num}", (year, num)


def discover_issues(data_dir):
    """Return a sorted list of issue dicts found under data_dir."""
    issues = []
    if not os.path.isdir(data_dir):
        return issues
    for name in sorted(os.listdir(data_dir)):
        issue_dir = os.path.join(data_dir, name)
        manifest_path = os.path.join(issue_dir, "manifest.json")
        if not os.path.isfile(manifest_path):
            continue
        manifest = load_json(manifest_path)
        if not manifest:
            log(f"skipping {name}: unreadable manifest")
            continue
        headline, date = parse_comments(manifest.get("version_comments"))
        issue_id = manifest.get("issue_id") or name
        label, sort_key = issue_label(issue_id)
        issues.append({
            "id": issue_id,
            "label": label,
            "sort_key": sort_key,
            "dir": issue_dir,
            "manifest": manifest,
            "title": manifest.get("title") or headline or name,
            "headline": headline,
            "date": date,
            "comments": manifest.get("version_comments") or "",
        })
    issues.sort(key=lambda i: i["sort_key"])
    return issues


class Launcher:
    """The main application window (the Tk root)."""

    def __init__(self, data_dir, scale="auto", restore=True):
        self.data_dir = data_dir
        self.restore = restore
        self.root = tk.Tk()
        self.root.title("El Radiaktivo Newz -- Colección")
        theme.init_scale(self.root, scale)
        theme.init_theme(self.root)
        self.session = None
        self.issues = discover_issues(data_dir)

        # -- search (§2) -------------------------------------------------
        self._search_index = search.SearchIndex(data_dir)
        self._search_window = None

        # -- session persistence (§3) --------------------------------------
        self._current_issue_id = None
        self._last_open_forms: list[str] = []
        self._loaded_state = state.load_state() if restore else None

        # -- keyboard accessibility (§4) ------------------------------------
        self._focus_rows: list[tk.Widget] = []

        self._build_ui()
        self._install_close_handler()
        self.root.bind("<Control-f>", lambda e: self.open_search())
        self.root.bind("<Control-F>", lambda e: self.open_search())

    # -- UI ------------------------------------------------------------------
    def _build_ui(self):
        self.root.configure(bg=theme.BUTTON_FACE)
        self.root.geometry(f"{theme.s(440)}x{theme.s(460)}")
        self.root.minsize(theme.s(360), theme.s(320))

        # Title bar band (teal desktop accent + white heading)
        header = tk.Frame(self.root, bg=theme.ACTIVE_TITLE, height=theme.s(54))
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="El Radiaktivo Newz",
                 font=theme.ui_font(14, bold=True),
                 fg="#FFFFFF", bg=theme.ACTIVE_TITLE).pack(anchor="w", padx=10,
                                                           pady=(6, 0))
        tk.Label(header, text="e-zine hacker mexicana  ·  1998-2000",
                 font=theme.ui_font(8), fg="#C0C0C0",
                 bg=theme.ACTIVE_TITLE).pack(anchor="w", padx=10)

        # sunken panel that holds the issue list (classic inset look)
        body = tk.Frame(self.root, bg=theme.BUTTON_FACE, bd=0)
        body.pack(side="top", fill="both", expand=True, padx=8, pady=8)

        tk.Label(body, text="Selecciona un número:",
                 font=theme.ui_font(8), bg=theme.BUTTON_FACE,
                 fg=theme.WINDOW_TEXT).pack(anchor="w", pady=(0, 4))

        panel = tk.Frame(body, bg=theme.WINDOW, bd=2, relief="sunken")
        panel.pack(side="top", fill="both", expand=True)

        canvas = tk.Canvas(panel, bg=theme.WINDOW, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        self._list_frame = tk.Frame(canvas, bg=theme.WINDOW)
        self._list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._list_frame, anchor="nw",
                             width=1)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._canvas = canvas
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure("all", width=e.width))

        self._populate_list()

        # status / footer
        footer = tk.Frame(self.root, bg=theme.BUTTON_FACE)
        footer.pack(side="bottom", fill="x", padx=8, pady=(0, 8))
        count = len(self.issues)
        self.status = tk.Label(
            footer,
            text=(f"{count} número(s) en «{os.path.basename(self.data_dir)}»"
                  if count else
                  f"Sin números en «{self.data_dir}»"),
            font=theme.ui_font(8), bg=theme.BUTTON_FACE, anchor="w",
            bd=1, relief="sunken", padx=4)
        self.status.pack(side="left", fill="x", expand=True)
        tk.Button(footer, text="Salir", font=theme.ui_font(8),
                  bg=theme.BUTTON_FACE, relief="raised", bd=2, width=10,
                  command=lambda: self._on_app_close()).pack(
            side="right", padx=(6, 0))
        tk.Button(footer, text="Buscar…", font=theme.ui_font(8),
                  bg=theme.BUTTON_FACE, relief="raised", bd=2, width=10,
                  command=self.open_search).pack(side="right", padx=(6, 0))

    def _populate_list(self):
        if self._loaded_state:
            issue = self._find_issue(self._loaded_state.get("last_issue"))
            if issue is not None:
                self._add_continue_row(issue)
        if not self.issues:
            tk.Label(self._list_frame,
                     text="No se encontraron números.\n"
                          "Genera data/ con el extractor (Fase 1).",
                     font=theme.ui_font(9), bg=theme.WINDOW, fg="#606060",
                     justify="left", padx=12, pady=20).pack(anchor="w")
            return
        for issue in self.issues:
            self._add_issue_row(issue)

    def _add_continue_row(self, issue):
        """Highlighted row offering to resume the last session (§3). Never
        acts without an explicit click -- nothing reopens automatically."""
        row = tk.Frame(self._list_frame, bg=theme.HIGHLIGHT, bd=0,
                       highlightthickness=0)
        row.pack(fill="x", padx=2, pady=1)

        inner = tk.Frame(row, bg=theme.HIGHLIGHT)
        inner.pack(fill="x", padx=6, pady=4)

        tk.Label(inner, text="Continuar donde te quedaste:",
                 font=theme.ui_font(8), bg=theme.HIGHLIGHT,
                 fg="#D0D0FF", anchor="w").pack(anchor="w", fill="x")
        tk.Label(inner, text=issue["label"],
                 font=theme.ui_font(10, bold=True), bg=theme.HIGHLIGHT,
                 fg="#FFFFFF", anchor="w").pack(anchor="w", fill="x")

        sep = tk.Frame(self._list_frame, bg="#D8D8D8", height=1)
        sep.pack(fill="x")

        widgets = [row, inner]

        def on_click(_=None):
            self._continue_last_session()

        for w in widgets:
            w.bind("<Button-1>", on_click)
            w.bind("<Double-Button-1>", on_click)
            try:
                w.configure(cursor="hand2")
            except tk.TclError:
                pass

        self._register_focus_row(widgets, self._continue_last_session,
                                 prepend=True, blur_color=theme.HIGHLIGHT,
                                 focus_color="#FFD700")

    def _add_issue_row(self, issue):
        row = tk.Frame(self._list_frame, bg=theme.WINDOW, bd=0,
                       highlightthickness=0)
        row.pack(fill="x", padx=2, pady=1)

        inner = tk.Frame(row, bg=theme.WINDOW)
        inner.pack(fill="x", padx=6, pady=4)

        title = tk.Label(inner, text=issue["title"],
                         font=theme.ui_font(10, bold=True), bg=theme.WINDOW,
                         fg=theme.ACTIVE_TITLE, anchor="w")
        title.pack(anchor="w", fill="x")

        sub = issue["date"] or issue["comments"]
        subtitle = tk.Label(inner, text=f"{issue['label']}   ·   {sub}",
                            font=theme.ui_font(8), bg=theme.WINDOW,
                            fg="#404040", anchor="w")
        subtitle.pack(anchor="w", fill="x")

        sep = tk.Frame(self._list_frame, bg="#D8D8D8", height=1)
        sep.pack(fill="x")

        widgets = [row, inner, title, subtitle]

        def on_enter(_=None):
            for w in widgets:
                w.configure(bg=theme.HIGHLIGHT)
            title.configure(fg="#FFFFFF")
            subtitle.configure(fg="#D0D0FF")

        def on_leave(_=None):
            for w in widgets:
                w.configure(bg=theme.WINDOW)
            title.configure(fg=theme.ACTIVE_TITLE)
            subtitle.configure(fg="#404040")

        def on_click(_=None):
            self.open_issue(issue)

        for w in widgets:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)
            w.bind("<Double-Button-1>", on_click)
            try:
                w.configure(cursor="hand2")
            except tk.TclError:
                pass

        self._register_focus_row(widgets, lambda: self.open_issue(issue))

    # -- keyboard accessibility (§4) -------------------------------------
    def _register_focus_row(self, widgets, on_activate, prepend=False,
                            blur_color=None, focus_color=None):
        """Make ``widgets[0]`` a Tab stop that represents one list row:
        Up/Down move focus between rows, Enter activates it, and a visible
        focus ring is drawn (in addition to the mouse hover/click that
        already works)."""
        row = widgets[0]
        blur_color = blur_color if blur_color is not None else theme.WINDOW
        focus_color = focus_color if focus_color is not None else theme.HIGHLIGHT
        row.configure(takefocus=1, highlightthickness=theme.s(2),
                     highlightbackground=blur_color,
                     highlightcolor=focus_color)

        def on_focus_in(_=None):
            row.configure(highlightbackground=focus_color)

        def on_focus_out(_=None):
            row.configure(highlightbackground=blur_color)

        def on_activate_key(_=None):
            on_activate()
            return "break"

        def on_up(_=None):
            self._move_row_focus(row, -1)
            return "break"

        def on_down(_=None):
            self._move_row_focus(row, 1)
            return "break"

        row.bind("<FocusIn>", on_focus_in)
        row.bind("<FocusOut>", on_focus_out)
        row.bind("<Return>", on_activate_key)
        row.bind("<Up>", on_up)
        row.bind("<Down>", on_down)

        if prepend:
            self._focus_rows.insert(0, row)
        else:
            self._focus_rows.append(row)

    def _move_row_focus(self, current, delta):
        if current not in self._focus_rows:
            return
        idx = self._focus_rows.index(current)
        target = self._focus_rows[min(max(idx + delta, 0),
                                      len(self._focus_rows) - 1)]
        target.focus_set()
        self._ensure_row_visible(target)

    def _ensure_row_visible(self, row):
        try:
            self._canvas.update_idletasks()
            total_h = max(self._list_frame.winfo_height(), 1)
            top_frac = row.winfo_y() / total_h
            bottom_frac = (row.winfo_y() + row.winfo_height()) / total_h
            lo, hi = self._canvas.yview()
            if top_frac < lo:
                self._canvas.yview_moveto(top_frac)
            elif bottom_frac > hi:
                self._canvas.yview_moveto(max(0.0, bottom_frac - (hi - lo)))
        except tk.TclError:
            pass

    # -- issue lifecycle -----------------------------------------------------
    def open_issue(self, issue):
        if self.session is not None:
            # already inside an issue; ignore
            return
        self.root.withdraw()
        self._current_issue_id = issue["id"]
        self._last_open_forms = []
        self.session = IssueSession(self.root, issue["dir"], issue["manifest"],
                                    on_closed=self._issue_closed)
        self._wrap_session_tracking(self.session)
        self.session.start()
        # If the issue could not open a single form, come straight back.
        if not self.session.open_forms:
            self._issue_closed(self.session)

    def open_issue_form(self, issue_id, form_name):
        """Like :meth:`open_issue` but shows one specific form directly
        (``session.show_form`` instead of ``session.start``). Used by the
        search window (§2) and by session restore (§3)."""
        issue = self._find_issue(issue_id)
        if issue is None:
            log(f"open_issue_form: unknown issue {issue_id!r}")
            return
        if self.session is not None:
            if self._current_issue_id == issue_id:
                self.session.show_form(form_name)
            else:
                log("open_issue_form: another issue is already open; ignoring")
            return
        self.root.withdraw()
        self._current_issue_id = issue_id
        self._last_open_forms = []
        self.session = IssueSession(self.root, issue["dir"], issue["manifest"],
                                    on_closed=self._issue_closed)
        self._wrap_session_tracking(self.session)
        self.session.show_form(form_name)
        if not self.session.open_forms:
            self._issue_closed(self.session)

    def _wrap_session_tracking(self, session):
        """Keep ``self._last_open_forms`` (and the persisted state) in sync
        with whatever forms get shown during the session, without touching
        engine.py: wrap the instance's own ``show_form`` bound method."""
        original_show_form = session.show_form

        def tracked_show_form(name, modal=False):
            result = original_show_form(name, modal=modal)
            self._last_open_forms = list(session.open_forms.keys())
            self._save_state()
            return result

        session.show_form = tracked_show_form

    def _issue_closed(self, session):
        self.session = None
        self._save_state()
        try:
            self.root.deiconify()
            self.root.lift()
        except tk.TclError:
            pass

    def _find_issue(self, issue_id):
        return next((i for i in self.issues if i["id"] == issue_id), None)

    # -- search (§2) -----------------------------------------------------
    def open_search(self):
        if self._search_window is not None:
            try:
                if self._search_window.top.winfo_exists():
                    self._search_window.focus()
                    return
            except tk.TclError:
                pass
        self._search_window = search.SearchWindow(
            self.root, self._search_index, on_open=self._on_search_result,
            label_fn=lambda issue_id: issue_label(issue_id)[0])

    def _on_search_result(self, issue_id, form_name):
        self.open_issue_form(issue_id, form_name)

    # -- session persistence (§3) -----------------------------------------
    def _save_state(self):
        if not self._current_issue_id:
            return
        state.save_state({
            "last_issue": self._current_issue_id,
            "open_forms": list(self._last_open_forms),
            "ts": time.time(),
        })

    def _continue_last_session(self):
        saved = self._loaded_state
        if not saved:
            return
        issue = self._find_issue(saved.get("last_issue"))
        if issue is None:
            return
        open_forms = list(saved.get("open_forms") or [])
        startup = issue["manifest"].get("startup_form")
        ordered = []
        if startup and startup in open_forms:
            ordered.append(startup)
        for name in open_forms:
            if name not in ordered:
                ordered.append(name)
        if not ordered and startup:
            ordered.append(startup)
        if not ordered:
            return
        self.open_issue_form(issue["id"], ordered[0])
        for name in ordered[1:]:
            if self.session is not None:
                self.session.show_form(name)

    def _install_close_handler(self):
        """Save state on app exit, whichever way it happens (window-manager
        close button, or the "Salir" button). Chains any WM_DELETE_WINDOW
        handler that might already be set on the root."""
        previous = self.root.protocol("WM_DELETE_WINDOW")

        def handler():
            self._save_state()
            if previous:
                try:
                    self.root.tk.call(previous)
                    return
                except tk.TclError:
                    pass
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", handler)
        self._on_app_close = handler

    def run(self):
        self.root.mainloop()
