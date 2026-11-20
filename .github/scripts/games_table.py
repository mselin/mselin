#!/usr/bin/env python3
"""The games in the table on the profile page, kept the same as on the homepage.

The homepage's repository (mselin/mselin.github.io) holds games.json and publishes it with the site. This
writes the profile README's game rows from it, in the same form as `games.py --markdown` there.

  games_table.py --check     fail if README.md's game rows differ from the published games.json (CI)
  games_table.py             rewrite README.md's game rows from it
  --games FILE               read a local games.json instead of the published one

A game's row is the table row whose first cell links to where the game is played. Standard library only.
"""

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URL = "https://mselin.github.io/games.json"


def fetch(url=URL):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "profile-ci"}), timeout=30) as r:
        return json.load(r)["games"]


def row(g):
    return f'| **[{g["name"]}]({g["play"]})** | {g["summary"]} [Play it]({g["play"]}) · [Source]({g["source"]}) |'


def is_row_of(line, g):
    """Whether a README line is the row for game `g`: its first cell links to where the game is played."""
    return line.startswith("| **[") and f']({g["play"]})**' in line.split(" | ")[0]


def rewrite(readme, games):
    """The README with each game's row written from `games`; a game with no row yet goes after the others."""
    lines = readme.split("\n")
    last = None
    for g in games:
        found = False
        for i, line in enumerate(lines):
            if is_row_of(line, g):
                lines[i] = row(g)
                last = i if last is None or i > last else last
                found = True
        if not found:
            if last is None:
                raise ValueError(f'README.md has no games table to add "{g["name"]}" to')
            lines.insert(last + 1, row(g))
            last += 1
    return "\n".join(lines)


def main(argv):
    games = json.loads(Path(argv[argv.index("--games") + 1]).read_text())["games"] if "--games" in argv else fetch()
    path = ROOT / "README.md"
    readme = path.read_text(encoding="utf-8")
    want = rewrite(readme, games)
    if "--check" in argv:
        if readme != want:
            print(f"README.md's game rows differ from {URL}: run python3 .github/scripts/games_table.py",
                  file=sys.stderr)
            return 1
        print(f"README.md's game rows match the homepage's games.json ({len(games)} games)")
        return 0
    path.write_text(want, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
