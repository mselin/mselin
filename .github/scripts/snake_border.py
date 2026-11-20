#!/usr/bin/env python3
"""Put a ring of empty cells round the contribution grid in Platane/snk's SVGs, and fill any gap inside it.

The snake's path runs one cell outside the grid at times (above it, or past its right edge), so it looks as if
it crawls off the board. With one ring of empty cells round the grid, every square the snake passes through is a
cell. The ring cells use the same class as empty grid cells, so they take the same colours in light and dark mode.

Usage: snake_border.py FILE.svg [FILE.svg ...]   (edits the files in place)
"""

import re
import sys

CELL = 16  # distance between cells in snk's output
SIZE = 12  # width and height of one cell


def add_ring(svg):
    cells = re.findall(r'<rect class="c[^"]*" x="(-?[\d.]+)" y="(-?[\d.]+)"', svg)
    if not cells:
        raise ValueError("no grid cells found")
    xs = sorted({round(float(x)) for x, _ in cells})
    ys = sorted({round(float(y)) for _, y in cells})
    left, right = xs[0] - CELL, xs[-1] + CELL
    top, bottom = ys[0] - CELL, ys[-1] + CELL

    # The ring, plus any gap inside it: the current week's column stops at today, which would leave a notch.
    have = {(round(float(x)), round(float(y))) for x, y in cells}
    ring = [
        (x, y)
        for x in range(left, right + 1, CELL)
        for y in range(top, bottom + 1, CELL)
        if (x, y) not in have
    ]
    rects = "".join(f'<rect class="c" x="{x}" y="{y}" rx="2" ry="2"/>' for x, y in ring)
    first = svg.index('<rect class="c')
    svg = svg[:first] + rects + svg[first:]

    # snk leaves a margin round the grid that the ring normally fits in; widen the picture if it does not.
    match = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"', svg)
    x0, y0, w, h = map(float, match.groups())
    nx0, ny0 = min(x0, left - 2), min(y0, top - 2)
    nx1, ny1 = max(x0 + w, right + SIZE + 2), max(y0 + h, bottom + SIZE + 2)
    if (nx0, ny0, nx1, ny1) != (x0, y0, x0 + w, y0 + h):
        nw, nh = nx1 - nx0, ny1 - ny0
        svg = svg.replace(match.group(0), f'viewBox="{nx0:g} {ny0:g} {nw:g} {nh:g}"', 1)
        svg = re.sub(r'(<svg[^>]*?) width="[\d.]+"', rf'\1 width="{nw:g}"', svg, count=1)
        svg = re.sub(r'(<svg[^>]*?) height="[\d.]+"', rf'\1 height="{nh:g}"', svg, count=1)
    return svg, len(ring)


def main(paths):
    for path in paths:
        with open(path, encoding="utf-8") as f:
            svg, added = add_ring(f.read())
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"{path}: added {added} empty cells")


if __name__ == "__main__":
    main(sys.argv[1:])
