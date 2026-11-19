#!/usr/bin/env python3
"""Repository sanity checks run by CI.

Checks every file tracked by git:
  * JSON files parse, SVG files are well-formed XML.
  * Local links and file references in HTML and Markdown point at files that exist,
    and in-page #anchors in HTML point at an id on that page.
  * No private network addresses (10.x, 172.16-31.x, 192.168.x).
  * None of the terms in the PRIVATE_TERMS environment variable (one per line), for
    host names, domains and the like that must stay off public pages. Set it as a
    repository secret. Matches are reported by file and line only, never by term,
    because Actions logs on a public repository are public.

Uses only the Python standard library. Exits non-zero if anything fails.
"""

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
FILES = [p for p in subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, text=True).split("\0") if p]
TRACKED = set(FILES)

PRIVATE_IP = re.compile(
    r"(?<![\d.])(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}(?![\d.])"
)
MD_LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
MD_HTML_REF = re.compile(r"\b(?:src|href|srcset)\s*=\s*\"([^\"]+)\"")
EXTERNAL = ("http:", "https:", "mailto:", "tel:", "data:", "javascript:", "//")

errors = []


def fail(path, line, message):
    errors.append(f"{path}:{line}: {message}" if line else f"{path}: {message}")


def read_text(rel):
    data = (ROOT / rel).read_bytes()
    if b"\0" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def is_dir(rel):
    prefix = "" if rel == "." else rel + "/"
    return any(f.startswith(prefix) for f in TRACKED)


def check_local_ref(src, line, ref, ids=None):
    """ids is the set of element ids for HTML pages, None for Markdown."""
    ref = ref.strip()
    if not ref or ref.startswith(EXTERNAL) or "{{" in ref or "${" in ref:
        return
    parts = urlsplit(ref)
    if parts.scheme:
        return
    if not parts.path:
        if ids is not None and parts.fragment and unquote(parts.fragment) not in ids:
            fail(src, line, f"link to #{parts.fragment}, but no element on the page has that id")
        return
    path = unquote(parts.path)
    base = ROOT if path.startswith("/") else (ROOT / src).parent
    try:
        rel = (base / path.lstrip("/")).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        fail(src, line, f"reference outside the repository: {ref}")
        return
    if rel in TRACKED:
        return
    if is_dir(rel):
        # A web server needs an index page for a folder; GitHub can show a folder from Markdown.
        index = "index.html" if rel == "." else rel + "/index.html"
        if ids is not None and index not in TRACKED:
            fail(src, line, f"link to a folder with no index.html: {ref}")
        return
    fail(src, line, f"reference to a file that is not in the repository: {ref}")


class RefCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        line = self.getpos()[0]
        for name, value in attrs:
            if value is None:
                continue
            if name == "id":
                self.ids.add(value)
            elif name in ("href", "src"):
                self.refs.append((line, value))
            elif name == "srcset":
                for candidate in value.split(","):
                    self.refs.append((line, candidate.strip().split(" ")[0]))

    handle_startendtag = handle_starttag


def main():
    terms = [t.strip().lower() for t in os.environ.get("PRIVATE_TERMS", "").splitlines() if t.strip()]
    term_patterns = [re.compile(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", re.I) for t in terms]

    for rel in FILES:
        if not (ROOT / rel).is_file():
            continue
        suffix = Path(rel).suffix.lower()
        text = read_text(rel)

        if suffix == ".json":
            try:
                json.loads(text or "")
            except ValueError as err:
                fail(rel, None, f"invalid JSON: {err}")
        elif suffix == ".svg":
            try:
                ET.fromstring(text or "")
            except ET.ParseError as err:
                fail(rel, None, f"SVG is not well-formed XML: {err}")

        if text is None:
            continue

        if suffix in (".html", ".htm"):
            collector = RefCollector()
            collector.feed(text)
            for line, ref in collector.refs:
                check_local_ref(rel, line, ref, collector.ids)
        elif suffix == ".md":
            for n, line_text in enumerate(text.splitlines(), 1):
                for match in MD_LINK.finditer(line_text):
                    check_local_ref(rel, n, match.group(1))
                for match in MD_HTML_REF.finditer(line_text):
                    check_local_ref(rel, n, match.group(1).split(" ")[0])

        if rel.endswith("package-lock.json"):
            continue
        for n, line_text in enumerate(text.splitlines(), 1):
            if PRIVATE_IP.search(line_text):
                fail(rel, n, "private network address")
            if any(p.search(line_text) for p in term_patterns):
                fail(rel, n, "matches an entry in PRIVATE_TERMS")

    if errors:
        print(f"{len(errors)} problem(s) found:")
        print("\n".join(errors))
        return 1
    note = f", {len(terms)} private term(s)" if terms else ", PRIVATE_TERMS not set"
    print(f"OK: {len(FILES)} tracked files checked{note}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
