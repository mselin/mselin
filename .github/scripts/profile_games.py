#!/usr/bin/env python3
"""Draw the two animated pictures on the profile page.

  snake.svg, snake-dark.svg   A game of Snake on the contribution graph. Contribution days are the food, each
                              one a segment longer; apples appear once they are gone, and a simple
                              computer player steers. It is good, not perfect: sooner or later it boxes itself
                              in and crashes, and the game starts again.
  life.svg, life-dark.svg     Conway's Game of Life on a grid the same size, from a random start, until it settles.

A README cannot run scripts, so each game is played out here and drawn as an SVG with CSS animation.
Standard library only.

  profile_games.py --user NAME --out DIR          fetch the calendar with GITHUB_TOKEN (GitHub Actions)
  profile_games.py --calendar FILE --out DIR      use a saved calendar: {"levels": [[0-4 or null] * 7] * 53}
  --seed N                                        repeat a run (the seed used is written into each picture)
"""

import argparse
import json
import os
import random
import sys
import urllib.request
from collections import deque

COLS, ROWS = 53, 7  # weeks by days, as on the contribution graph
PITCH, SIZE = 16, 12  # distance between cells, and cell size, in pixels
WIDTH, HEIGHT = 880, 148  # (COLS + 2) * PITCH = 880; the board has a wall all round

SNAKE_STEP = 0.07  # seconds per move
SNAKE_HOLD = 3.0  # seconds the crash stays on screen
SNAKE_MAX_STEPS = 1200  # then it carries straight on until it hits something
APPLE_GROWTH = 2
CAREFUL = 0.7  # the player takes a move only if it leaves room for this share of its length
TIRED_AFTER = 700  # moves; after this the player stops looking ahead, so a long game still ends in a crash

LIFE_STEP = 0.22  # seconds per generation
LIFE_HOLD = 2.0
LIFE_MAX_GENERATIONS = 150
LIFE_MIN_GENERATIONS = 60
LIFE_DENSITY = 0.32

PALETTES = {
    "light": {
        "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "wall": "#d0d7de",
        "snake": "#8250df",
        "head": "#6639ba",
        "apple": "#cf222e",
        "crash": "#cf222e",
        "text": "#24292f",
        "panel": "#ffffffd9",
        "life": "#40c463",
    },
    "dark": {
        "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "wall": "#30363d",
        "snake": "#5cc8ff",
        "head": "#a5e0ff",
        "apple": "#f85149",
        "crash": "#f85149",
        "text": "#e6edf3",
        "panel": "#0d1117d9",
        "life": "#39d353",
    },
}

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]


# ---------- the contribution calendar ----------


def fetch_calendar(user, token):
    """Contribution levels by [week][weekday], 0-4, None for days outside the calendar (later this week)."""
    query = (
        "query($login:String!){user(login:$login){contributionsCollection{contributionCalendar"
        "{weeks{contributionDays{weekday contributionLevel}}}}}}"
    )
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(f"GraphQL error: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"][-COLS:]
    levels = [[None] * ROWS for _ in range(COLS)]
    offset = COLS - len(weeks)
    for c, week in enumerate(weeks):
        for day in week["contributionDays"]:
            levels[offset + c][day["weekday"]] = LEVELS[day["contributionLevel"]]
    return levels


# ---------- shared drawing helpers ----------


def px(c, r):
    """Top-left corner of board cell (c, r); the wall is at c = -1 and c = COLS, r = -1 and r = ROWS."""
    return (c + 1) * PITCH + 2, (r + 1) * PITCH + 2


def pct(t, total):
    """A keyframe position, with just enough decimals to tell one step from the next."""
    decimals = max(1, len(str(int(total))) - 1)
    return f"{100 * t / total:.{decimals}f}".rstrip("0").rstrip(".") + "%"


def step_keyframes(name, prop, changes, total):
    """Keyframes that hold each value until the next change. changes: [(time, value)], starting at time 0.
    Times with the same value share one rule, which keeps long animations small."""
    times = {}
    for t, v in changes:
        times.setdefault(v, []).append(pct(t, total))
    rules = "".join(f"{','.join(ts)}{{{prop}:{v}}}" for v, ts in times.items())
    return f"@keyframes {name}{{{rules}}}"


def grid(pattern_id, fill, x=0, y=0, width=WIDTH, height=(ROWS + 2) * PITCH):
    """A block of cells drawn by one SVG pattern, instead of one element per cell."""
    return (
        f'<defs><pattern id="{pattern_id}" width="{PITCH}" height="{PITCH}" patternUnits="userSpaceOnUse">'
        f'<rect x="2" y="2" width="{SIZE}" height="{SIZE}" rx="2" fill="{fill}"/></pattern></defs>'
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="url(#{pattern_id})"/>'
    )


CELL_CSS = f".q{{width:{SIZE}px;height:{SIZE}px;rx:2px;ry:2px}}"


def svg_document(desc, style, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" '
        f'height="{HEIGHT}"><desc>{desc}</desc><style>{CELL_CSS}{style}'
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        f"</style>{body}</svg>"
    )


# ---------- Snake ----------


def free_area(start, blocked):
    """How many free cells can be reached from start, not counting start."""
    seen, queue = {start}, deque([start])
    while queue:
        c, r = queue.popleft()
        for dc, dr in DIRS:
            n = (c + dc, r + dr)
            if 0 <= n[0] < COLS and 0 <= n[1] < ROWS and n not in seen and n not in blocked:
                seen.add(n)
                queue.append(n)
    return len(seen) - 1


def food_distance(start, blocked, targets):
    """Moves from start to the nearest target, or None if none can be reached."""
    if start in targets:
        return 0
    seen, queue = {start}, deque([(start, 0)])
    while queue:
        (c, r), d = queue.popleft()
        for dc, dr in DIRS:
            n = (c + dc, r + dr)
            if 0 <= n[0] < COLS and 0 <= n[1] < ROWS and n not in seen and n not in blocked:
                if n in targets:
                    return d + 1
                seen.add(n)
                queue.append((n, d + 1))
    return None


def play_snake(levels, rng):
    """Play one game. Returns the head's path, the length after each move, and what was eaten when."""
    start = [(2, ROWS // 2), (1, ROWS // 2), (0, ROWS // 2)]
    food = {(c, r): lv for c in range(COLS) for r in range(ROWS) if (lv := levels[c][r])}
    body = deque(start)
    occupied = set(body)
    eaten = {cell: 0 for cell in start if food.pop(cell, None)}
    apples = []  # {"cell", "born", "eaten"}
    path, lengths = [start[0]], [len(body)]
    heading, grow, crashed = (1, 0), 0, False

    def apple_now():
        return next((a for a in apples if a["eaten"] is None), None)

    def spawn_apple(step):
        free = [(c, r) for c in range(COLS) for r in range(ROWS) if (c, r) not in occupied]
        if free:
            apples.append({"cell": rng.choice(free), "born": step, "eaten": None})

    if not food:
        spawn_apple(0)

    step = 0
    while not crashed:
        step += 1
        head, tail = body[0], body[-1]
        if step > SNAKE_MAX_STEPS:
            # Out of time: carry straight on until it hits the wall or itself.
            n = (head[0] + heading[0], head[1] + heading[1])
            crashed = not (0 <= n[0] < COLS and 0 <= n[1] < ROWS) or (n in occupied and n != tail)
            if food.pop(n, None):
                eaten[n] = step
            apple = apple_now()
            if apple is not None and n == apple["cell"]:
                apple["eaten"] = step
            occupied.discard(body.pop())
            body.appendleft(n)
            occupied.add(n)
            path.append(n)
            lengths.append(len(body))
            continue
        apple = apple_now()
        targets = set(food) | ({apple["cell"]} if apple else set())
        options = []
        for d in DIRS:
            if d == (-heading[0], -heading[1]):
                continue
            n = (head[0] + d[0], head[1] + d[1])
            grows = grow > 0 or n in food or (apple is not None and n == apple["cell"])
            blocked = occupied if grows else occupied - {tail}
            if not (0 <= n[0] < COLS and 0 <= n[1] < ROWS) or n in blocked:
                continue
            after = blocked | {n}
            eats = n in food or (apple is not None and n == apple["cell"])
            length = len(body) + grow + (1 if eats else 0)  # including growth still to come
            options.append(
                {
                    "dir": d,
                    "cell": n,
                    "room": free_area(n, after),
                    "need": length * CAREFUL if step <= TIRED_AFTER else 0,
                    "dist": food_distance(n, after, targets),
                    "straight": d == heading,
                }
            )
        roomy = [o for o in options if o["room"] >= o["need"]]
        if roomy:
            choice = min(roomy, key=lambda o: (o["dist"] is None, o["dist"] or 0, not o["straight"]))
        elif options:
            choice = max(options, key=lambda o: (o["room"], o["straight"]))
        else:
            # Nowhere left to go: carry straight on into whatever is there.
            n = (head[0] + heading[0], head[1] + heading[1])
            choice, crashed = {"dir": heading, "cell": n}, True

        heading, n = choice["dir"], choice["cell"]
        if n in food:
            food.pop(n)
            grow += 1
            eaten[n] = step
        elif apple is not None and n == apple["cell"]:
            grow += APPLE_GROWTH
            apple["eaten"] = step
        if grow > 0:
            grow -= 1
        else:
            occupied.discard(body.pop())
        body.appendleft(n)
        occupied.add(n)
        path.append(n)
        lengths.append(len(body))
        if crashed:
            break
        if not food and apple_now() is None:
            spawn_apple(step)
    return {"path": path, "lengths": lengths, "eaten": eaten, "apples": apples, "start": start, "crashed": crashed}


def draw_snake(game, levels, palette, seed):
    p = PALETTES[palette]
    path, lengths, start = game["path"], game["lengths"], game["start"]
    moves = len(path) - 1
    hold = round(SNAKE_HOLD / SNAKE_STEP)
    lead = len(start) - 1  # steps before the start, for the body's first moves
    end = moves + hold  # the snake disappears here, and the board waits for the next game
    total = end + lead
    duration = f"{total * SNAKE_STEP:.2f}s"
    style = [f".t{{animation:{duration} step-end infinite}}"]
    body = []

    # Board: a wall all round, empty cells, and contribution cells, which go dark when eaten.
    body.append(grid("w", p["wall"]))
    body.append(grid("e", p["levels"][0], x=PITCH, y=PITCH, width=COLS * PITCH, height=ROWS * PITCH))
    for c in range(COLS):
        for r in range(ROWS):
            lv = levels[c][r] or 0
            if not lv:
                continue
            x, y = px(c, r)
            when = game["eaten"].get((c, r))
            if when is None:
                body.append(f'<rect class="q" x="{x}" y="{y}" fill="{p["levels"][lv]}"/>')
                continue
            name = f"e{len(style)}"
            style.append(step_keyframes(name, "fill", [(0, p["levels"][lv]), (when, p["levels"][0])], total))
            body.append(
                f'<rect class="q t" x="{x}" y="{y}" fill="{p["levels"][lv]}" style="animation-name:{name}"/>'
            )

    # Apples, each shown from when it appears until it is eaten (or the game ends).
    for a in game["apples"]:
        x, y = px(*a["cell"])
        gone = a["eaten"] if a["eaten"] is not None else end
        name = f"a{len(style)}"
        changes = [(0, 0), (a["born"], 1), (gone, 0)] if a["born"] else [(0, 1), (gone, 0)]
        style.append(step_keyframes(name, "opacity", changes, total))
        body.append(
            f'<circle class="t" cx="{x + SIZE // 2}" cy="{y + SIZE // 2}" r="5" fill="{p["apple"]}" '
            f'opacity="{0 if a["born"] else 1}" style="animation-name:{name}"/>'
        )

    # The head's path through one loop: the game, the crash held on screen, then the moves before the start.
    # Keyframes only where it turns: in between, it moves in a straight line at an even speed.
    def delta(u):
        return path[u + 1][0] - path[u][0], path[u + 1][1] - path[u][1]

    turns = [0] + [u for u in range(1, moves) if delta(u - 1) != delta(u)] + [moves]
    frames = [(u, path[u]) for u in turns] + [(end, path[-1]), (end + 0.01, start[lead])]
    frames += [(end + k, start[lead - k]) for k in range(1, lead)] + [(total, path[0])]
    keyframes = "".join(
        f"{pct(t, total)}{{transform:translate({px(*xy)[0]}px,{px(*xy)[1]}px)}}" for t, xy in frames
    )
    style.append(f"@keyframes m{{{keyframes}}}")
    style.append(
        f".s{{animation-duration:{duration};animation-iteration-count:infinite;"
        "animation-timing-function:linear,step-end}"
    )

    # Segment i follows the head's path i moves behind, and is shown once the snake is longer than i, until
    # the crash. It cannot stop there by itself (it would carry on along the path), so a still copy takes over.
    for i in range(max(lengths) - 1, -1, -1):
        first = next(u for u, n in enumerate(lengths) if n > i)
        name = f"v{i}"
        changes = [(0, 1), (moves, 0)] if first == 0 else [(0, 0), (first, 1), (moves, 0)]
        style.append(step_keyframes(name, "opacity", changes, total))
        x, y = px(*(start[i] if i < len(start) else path[0]))
        delay = f"{(i - total) * SNAKE_STEP:.2f}s" if i else "0s"
        body.append(
            f'<rect class="s" width="{SIZE}" height="{SIZE}" rx="{4 if i == 0 else 3}" '
            f'fill="{p["head"] if i == 0 else p["snake"]}" opacity="{1 if first == 0 else 0}" '
            f'style="transform:translate({x}px,{y}px);animation-name:m,{name};animation-delay:{delay},0s"/>'
        )

    # The crashed snake, still, from the crash until the board clears.
    style.append(step_keyframes("x", "opacity", [(0, 0), (moves, 1), (end, 0)], total))
    wreck = "".join(
        f'<rect x="{px(*path[moves - i])[0]}" y="{px(*path[moves - i])[1]}" width="{SIZE}" height="{SIZE}" '
        f'rx="{4 if i == 0 else 3}"/>'
        for i in range(lengths[-1] - 1, -1, -1)
    )
    body.append(f'<g class="t" fill="{p["crash"]}" opacity="0" style="animation-name:x">{wreck}</g>')

    # Game over.
    style.append(step_keyframes("g", "opacity", [(0, 0), (moves, 1), (end, 0)], total))
    body.append(
        f'<g class="t" opacity="0" style="animation-name:g">'
        f'<rect x="{WIDTH // 2 - 170}" y="{HEIGHT // 2 - 22}" width="340" height="40" rx="6" fill="{p["panel"]}"/>'
        f'<text x="{WIDTH // 2}" y="{HEIGHT // 2 + 5}" text-anchor="middle" fill="{p["text"]}" '
        'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="20" font-weight="700">'
        f"GAME OVER · LENGTH {lengths[-1]}</text></g>"
    )
    desc = f"Snake on the contribution graph, played by the computer. Seed {seed}."
    return svg_document(desc, "".join(style), "".join(body))


# ---------- Game of Life ----------

LIFE_COLS, LIFE_ROWS = COLS + 2, ROWS + 2  # the same size as the snake board with its wall


def life_step(alive):
    counts = {}
    for c, r in alive:
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc or dr:
                    n = ((c + dc) % LIFE_COLS, (r + dr) % LIFE_ROWS)
                    counts[n] = counts.get(n, 0) + 1
    return frozenset(n for n, k in counts.items() if k == 3 or (k == 2 and n in alive))


def play_life(rng):
    """From a random start, run until the pattern dies, repeats or runs long. Tries a few starts, keeps the longest."""
    best = None
    for _ in range(30):
        alive = frozenset(
            (c, r) for c in range(LIFE_COLS) for r in range(LIFE_ROWS) if rng.random() < LIFE_DENSITY
        )
        history, seen = [alive], {alive}
        while len(history) <= LIFE_MAX_GENERATIONS:
            alive = life_step(alive)
            if alive in seen or not alive:
                if not alive:
                    history.append(alive)
                break
            history.append(alive)
            seen.add(alive)
        if best is None or len(history) > len(best):
            best = history
        if len(best) >= LIFE_MIN_GENERATIONS:
            break
    return best


def draw_life(history, palette, seed):
    p = PALETTES[palette]
    gens = len(history)
    total = gens + round(LIFE_HOLD / LIFE_STEP)
    duration = f"{total * LIFE_STEP:.2f}s"
    style = [f".a{{fill:{p['life']};animation:{duration} step-end infinite}}"]
    body = [grid("e", p["levels"][0], width=LIFE_COLS * PITCH, height=LIFE_ROWS * PITCH)]
    names = {}
    for c in range(LIFE_COLS):
        for r in range(LIFE_ROWS):
            changes, state = [], None
            for g, alive in enumerate(history):
                now = 1 if (c, r) in alive else 0
                if now != state:
                    changes.append((g, now))
                    state = now
            if changes == [(0, 0)]:
                continue
            key = tuple(changes)
            if key not in names:
                names[key] = f"l{len(names)}"
                style.append(step_keyframes(names[key], "opacity", changes, total))
            body.append(
                f'<rect class="q a" x="{c * PITCH + 2}" y="{r * PITCH + 2}" opacity="{changes[0][1]}" '
                f'style="animation-name:{names[key]}"/>'
            )
    desc = f"Conway's Game of Life from a random start, {gens} generations. Seed {seed}."
    return svg_document(desc, "".join(style), "".join(body))


# ---------- main ----------


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--user", help="GitHub user whose contribution calendar to fetch (needs GITHUB_TOKEN)")
    source.add_argument("--calendar", help="saved calendar JSON instead of fetching")
    parser.add_argument("--out", required=True, help="folder to write the SVG files to")
    parser.add_argument("--seed", type=int, help="random seed, to repeat a run")
    args = parser.parse_args(argv)

    if args.calendar:
        with open(args.calendar, encoding="utf-8") as f:
            levels = json.load(f)["levels"]
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("GITHUB_TOKEN is not set")
        levels = fetch_calendar(args.user, token)

    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(2**32)
    game = play_snake(levels, random.Random(seed))
    history = play_life(random.Random(seed))
    os.makedirs(args.out, exist_ok=True)
    for palette, suffix in (("light", ""), ("dark", "-dark")):
        for name, svg in (
            (f"snake{suffix}.svg", draw_snake(game, levels, palette, seed)),
            (f"life{suffix}.svg", draw_life(history, palette, seed)),
        ):
            with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
                f.write(svg)
    print(
        f"seed {seed}: snake made {len(game['path']) - 1} moves and crashed at length {game['lengths'][-1]}; "
        f"life ran {len(history)} generations"
    )


if __name__ == "__main__":
    main()
