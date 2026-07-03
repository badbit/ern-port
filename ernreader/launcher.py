"""The collection launcher: a classic Win95 window listing the issues.

Scans the data directory for ``<ISSUE>/manifest.json`` files, shows title and
date (parsed from ``version_comments``), and opens an issue's startup form when
chosen. Returning from an issue (last window closed, or ``quit``) re-shows it.
"""

from __future__ import annotations

import os
import re
import tkinter as tk

from . import theme
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

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.root = tk.Tk()
        self.root.title("El Radiaktivo Newz -- Colección")
        theme.init_theme(self.root)
        self.session = None
        self.issues = discover_issues(data_dir)
        self._build_ui()

    # -- UI ------------------------------------------------------------------
    def _build_ui(self):
        self.root.configure(bg=theme.BUTTON_FACE)
        self.root.geometry("440x460")
        self.root.minsize(360, 320)

        # Title bar band (teal desktop accent + white heading)
        header = tk.Frame(self.root, bg=theme.ACTIVE_TITLE, height=54)
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
                  bg=theme.BUTTON_FACE, relief="raised", bd=2,
                  width=10, command=self.root.destroy).pack(side="right",
                                                            padx=(6, 0))

    def _populate_list(self):
        if not self.issues:
            tk.Label(self._list_frame,
                     text="No se encontraron números.\n"
                          "Genera data/ con el extractor (Fase 1).",
                     font=theme.ui_font(9), bg=theme.WINDOW, fg="#606060",
                     justify="left", padx=12, pady=20).pack(anchor="w")
            return
        for issue in self.issues:
            self._add_issue_row(issue)

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

    # -- issue lifecycle -----------------------------------------------------
    def open_issue(self, issue):
        if self.session is not None:
            # already inside an issue; ignore
            return
        self.root.withdraw()
        self.session = IssueSession(self.root, issue["dir"], issue["manifest"],
                                    on_closed=self._issue_closed)
        self.session.start()
        # If the issue could not open a single form, come straight back.
        if not self.session.open_forms:
            self._issue_closed(self.session)

    def _issue_closed(self, session):
        self.session = None
        try:
            self.root.deiconify()
            self.root.lift()
        except tk.TclError:
            pass

    def run(self):
        self.root.mainloop()
