"""Full-text search across the whole collection (docs/FEATURES.md §2).

Builds a lazy, in-memory index over every issue's ``manifest.json``: one
document per form that has at least one "long" text control -- a control with
``text_file`` (its .txt is read from disk) or inline ``text`` longer than 200
chars, recursing into ``children`` (Frame/PictureBox containers). Matching is
substring-based over accent-folded, lower-cased text; several space-separated
terms are ANDed (all must appear, anywhere in the document).

This module is self-contained (only stdlib + ``theme`` for the UI) so it can
be unit-tested without touching the engine or the launcher.
"""

from __future__ import annotations

import os
import sys
import json
import unicodedata
import tkinter as tk
from dataclasses import dataclass, field

from . import theme


_INLINE_MIN_LEN = 200   # matches the extractor's threshold for text_file vs text
_SNIPPET_WIDTH = 80


def _log(msg: str) -> None:
    print(f"[ernreader] {msg}", file=sys.stderr)


def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        _log(f"search: could not read {path}: {exc}")
        return None


# --- normalization -----------------------------------------------------------

def normalize(text: str) -> str:
    """Lowercase and accent-fold (NFD, drop combining marks)."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _normalize_with_map(text: str):
    """Like :func:`normalize`, but also returns a list mapping each output
    character back to its index in the original ``text``, so a match found in
    the normalized string can be re-anchored in the original (accented,
    original-case) text for snippet extraction."""
    out = []
    idx_map = []
    for i, ch in enumerate(text):
        for dch in unicodedata.normalize("NFD", ch.lower()):
            if unicodedata.combining(dch):
                continue
            out.append(dch)
            idx_map.append(i)
    return "".join(out), idx_map


# --- index model ---------------------------------------------------------------

@dataclass
class Document:
    issue_id: str
    form_name: str
    title: str
    content: str
    norm_blob: str = field(default="", repr=False, compare=False)
    norm_content: str = field(default="", repr=False, compare=False)
    content_map: list = field(default_factory=list, repr=False, compare=False)

    def __post_init__(self):
        self.norm_content, self.content_map = _normalize_with_map(self.content)
        # searchable text includes the title and the internal form name too
        # (e.g. a form literally called "Telnor" should be found by that
        # word even if it never appears verbatim inside the article body).
        self.norm_blob = "\n".join((
            normalize(self.title), normalize(self.form_name), self.norm_content
        ))


@dataclass
class SearchResult:
    issue_id: str
    form_name: str
    title: str
    snippet: str


def _read_text_file(issue_dir: str, rel_path: str) -> str:
    if not rel_path:
        return ""
    path = os.path.join(issue_dir, rel_path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        _log(f"search: could not read text file {path}: {exc}")
        return ""


def _collect_texts(controls, issue_dir: str, out: list) -> None:
    for ctrl in controls or []:
        text_file = ctrl.get("text_file")
        if text_file:
            text = _read_text_file(issue_dir, text_file)
            if text:
                out.append(text)
        else:
            inline = ctrl.get("text")
            if inline and len(inline) > _INLINE_MIN_LEN:
                out.append(inline)
        _collect_texts(ctrl.get("children"), issue_dir, out)


def _iter_issue_dirs(data_dir: str):
    if not os.path.isdir(data_dir):
        return
    for name in sorted(os.listdir(data_dir)):
        issue_dir = os.path.join(data_dir, name)
        manifest_path = os.path.join(issue_dir, "manifest.json")
        if os.path.isfile(manifest_path):
            yield name, issue_dir, manifest_path


def build_index(data_dir: str) -> list:
    """Scan every ``<data_dir>/<issue>/manifest.json`` and build the list of
    searchable :class:`Document`. One document per form with qualifying text."""
    docs: list[Document] = []
    for name, issue_dir, manifest_path in _iter_issue_dirs(data_dir):
        manifest = _load_json(manifest_path)
        if not manifest:
            continue
        issue_id = manifest.get("issue_id") or name
        for form_name, form in (manifest.get("forms") or {}).items():
            parts: list[str] = []
            _collect_texts(form.get("controls"), issue_dir, parts)
            if not parts:
                continue
            title = form.get("caption") or form_name
            docs.append(Document(issue_id=issue_id, form_name=form_name,
                                  title=title, content="\n".join(parts)))
    return docs


def _make_snippet(doc: Document, terms, width: int = _SNIPPET_WIDTH) -> str:
    pos = -1
    for term in terms:
        p = doc.norm_content.find(term)
        if p != -1:
            pos = p
            break
    content = doc.content
    if pos == -1 or not doc.content_map:
        snippet = " ".join(content.split())
        if len(snippet) > width:
            snippet = snippet[:width].rstrip() + "…"
        return snippet
    orig_pos = doc.content_map[pos]
    half = width // 2
    start = max(0, orig_pos - half)
    end = min(len(content), orig_pos + half)
    snippet = " ".join(content[start:end].split())
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(content) else ""
    return f"{prefix}{snippet}{suffix}"


class SearchIndex:
    """Lazily-built, cached full-text index for one ``data_dir``."""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self._docs = None

    def ensure_built(self) -> list:
        if self._docs is None:
            self._docs = build_index(self.data_dir)
            _log(f"search: indexed {len(self._docs)} document(s) "
                 f"from {self.data_dir}")
        return self._docs

    def search(self, query: str, limit: int = 200) -> list:
        terms = [normalize(t) for t in (query or "").split() if t.strip()]
        if not terms:
            return []
        results = []
        for doc in self.ensure_built():
            if all(term in doc.norm_blob for term in terms):
                results.append(SearchResult(
                    issue_id=doc.issue_id, form_name=doc.form_name,
                    title=doc.title, snippet=_make_snippet(doc, terms)))
                if len(results) >= limit:
                    break
        return results


# --- UI: "Buscar en la colección" (Win95 look) --------------------------------

class SearchWindow:
    """Non-modal search window. Stays open while an article is being read."""

    def __init__(self, master, index: SearchIndex, on_open, label_fn):
        self.index = index
        self.on_open = on_open
        self.label_fn = label_fn
        self._results: list = []

        self.top = tk.Toplevel(master)
        self.top.title("Buscar en la colección")
        self.top.configure(bg=theme.FACE)
        self.top.geometry(f"{theme.s(440)}x{theme.s(360)}")
        self.top.minsize(theme.s(320), theme.s(240))
        try:
            self.top.transient(master)
        except tk.TclError:
            pass
        self.top.protocol("WM_DELETE_WINDOW", self.close)
        self.top.bind("<Escape>", lambda e: self.close())

        body = tk.Frame(self.top, bg=theme.FACE)
        body.pack(fill="both", expand=True,
                  padx=theme.s(8), pady=theme.s(8))

        entry_row = tk.Frame(body, bg=theme.FACE)
        entry_row.pack(fill="x", pady=(0, theme.s(6)))
        tk.Label(entry_row, text="Buscar:", font=theme.ui_font(8),
                 bg=theme.FACE, fg=theme.WINDOW_TEXT).pack(side="left")
        self.entry = tk.Entry(entry_row, font=theme.ui_font(9),
                              relief="sunken", bd=2)
        self.entry.pack(side="left", fill="x", expand=True,
                       padx=(theme.s(6), theme.s(6)))
        self.entry.bind("<Return>", lambda e: self._do_search())
        self.entry.bind("<Down>", self._focus_first_result)
        tk.Button(entry_row, text="Buscar", font=theme.ui_font(8),
                 bg=theme.FACE, relief="raised", bd=2, width=10,
                 command=self._do_search).pack(side="left")

        list_panel = tk.Frame(body, bg=theme.WINDOW, bd=2, relief="sunken")
        list_panel.pack(fill="both", expand=True)
        vsb = tk.Scrollbar(list_panel, orient="vertical")
        self.listbox = tk.Listbox(
            list_panel, font=theme.ui_font(9), bg=theme.WINDOW,
            fg=theme.WINDOW_TEXT, selectbackground=theme.HIGHLIGHT,
            selectforeground=theme.HIGHLIGHT_TEXT, activestyle="none",
            bd=0, highlightthickness=0, exportselection=False,
            yscrollcommand=vsb.set)
        vsb.configure(command=self.listbox.yview)
        self.listbox.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.listbox.bind("<Return>", lambda e: self._open_selected())
        self.listbox.bind("<Double-Button-1>", lambda e: self._open_selected())
        self.listbox.bind("<Escape>", lambda e: self.close())

        self.status = tk.Label(body, text="Escribe un término y pulsa Buscar",
                               font=theme.ui_font(8), bg=theme.FACE,
                               fg=theme.WINDOW_TEXT, anchor="w")
        self.status.pack(fill="x", pady=(theme.s(6), 0))

        self.entry.focus_set()

    # -- behaviour -------------------------------------------------------
    def _focus_first_result(self, _event=None):
        if self.listbox.size():
            self.listbox.focus_set()
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(0)
            self.listbox.activate(0)
        return "break"

    def _do_search(self):
        query = self.entry.get().strip()
        self.listbox.delete(0, "end")
        self._results = self.index.search(query) if query else []
        for r in self._results:
            label = self.label_fn(r.issue_id)
            line = f"{label} · {r.title} — {r.snippet}" if r.snippet \
                else f"{label} · {r.title}"
            self.listbox.insert("end", line)
        if not query:
            self.status.configure(text="Escribe un término y pulsa Buscar")
        else:
            n = len(self._results)
            self.status.configure(
                text=f"{n} resultado{'s' if n != 1 else ''}")

    def _open_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        result = self._results[sel[0]]
        self.on_open(result.issue_id, result.form_name)

    def close(self):
        try:
            self.top.destroy()
        except tk.TclError:
            pass

    def focus(self):
        try:
            self.top.deiconify()
            self.top.lift()
            self.entry.focus_set()
        except tk.TclError:
            pass
