"""Tests for profile_games.py. Run: python3 -m unittest discover -s .github/scripts"""

import random
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import profile_games as pg


def calendar(seed=7, busy=0.15):
    """A made-up contribution calendar, with the current week cut short as on GitHub."""
    rng = random.Random(seed)
    levels = [[rng.choice([1, 2, 3, 4]) if rng.random() < busy else 0 for _ in range(pg.ROWS)] for _ in range(pg.COLS)]
    levels[-1][4:] = [None] * (pg.ROWS - 4)
    return levels


class SnakeTest(unittest.TestCase):
    def test_games_follow_the_rules(self):
        for seed in range(6):
            levels = calendar(seed)
            game = pg.play_snake(levels, random.Random(seed))
            path, lengths = game["path"], game["lengths"]
            self.assertEqual(len(path), len(lengths))
            for a, b in zip(path, path[1:]):
                self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1, f"seed {seed}: the head jumped")
            for u in range(1, len(path)):
                self.assertLessEqual(lengths[u] - lengths[u - 1], 1, "grows at most one cell a move")
                # The body is the last `length` cells of the path; it only overlaps itself or leaves
                # the board on the crash move.
                body = path[u - lengths[u] + 1 : u + 1] if u - lengths[u] + 1 >= 0 else None
                if body is not None and u < len(path) - 1:
                    self.assertEqual(len(set(body)), len(body), f"seed {seed}: overlapped itself at move {u}")
                    self.assertTrue(all(0 <= c < pg.COLS and 0 <= r < pg.ROWS for c, r in body))
            eaten_days = set(game["eaten"])
            food_days = {(c, r) for c in range(pg.COLS) for r in range(pg.ROWS) if levels[c][r]}
            self.assertLessEqual(eaten_days, food_days)

    def test_the_player_crashes_sooner_or_later(self):
        for busy in (0.0, 0.02, 0.15):
            for seed in range(4):
                game = pg.play_snake(calendar(seed, busy), random.Random(seed))
                self.assertTrue(game["crashed"], "the game should end in a crash, so it can start again")
                end = game["path"][-1]
                hit_wall = not (0 <= end[0] < pg.COLS and 0 <= end[1] < pg.ROWS)
                hit_self = end in game["path"][-game["lengths"][-1] : -1]
                self.assertTrue(hit_wall or hit_self, f"the last move should hit something, not {end}")

    def test_an_empty_calendar_still_has_apples(self):
        levels = [[0] * pg.ROWS for _ in range(pg.COLS)]
        game = pg.play_snake(levels, random.Random(1))
        self.assertTrue(game["apples"])
        self.assertGreater(game["lengths"][-1], 3)

    def test_the_same_seed_plays_the_same_game(self):
        a = pg.play_snake(calendar(), random.Random(42))
        b = pg.play_snake(calendar(), random.Random(42))
        self.assertEqual(a["path"], b["path"])


class LifeTest(unittest.TestCase):
    def test_each_generation_follows_from_the_last(self):
        history = pg.play_life(random.Random(3))
        self.assertGreater(len(history), 1)
        for a, b in zip(history, history[1:]):
            self.assertEqual(pg.life_step(a), b)

    def test_a_blinker_blinks(self):
        blinker = frozenset({(5, 4), (6, 4), (7, 4)})
        self.assertEqual(pg.life_step(pg.life_step(blinker)), blinker)
        self.assertEqual(pg.life_step(blinker), frozenset({(6, 3), (6, 4), (6, 5)}))

    def test_cells_wrap_round_the_edges(self):
        across = frozenset({(pg.LIFE_COLS - 1, 4), (0, 4), (1, 4)})
        self.assertEqual(pg.life_step(across), frozenset({(0, 3), (0, 4), (0, 5)}))


class PicturesTest(unittest.TestCase):
    def test_writes_four_valid_svgs(self):
        with tempfile.TemporaryDirectory() as out:
            cal = Path(out) / "calendar.json"
            cal.write_text('{"levels": ' + str(calendar()).replace("None", "null") + "}")
            pg.main(["--calendar", str(cal), "--out", out, "--seed", "5"])
            for name in ("snake.svg", "snake-dark.svg", "life.svg", "life-dark.svg"):
                svg = (Path(out) / name).read_text()
                ET.fromstring(svg)
                self.assertIn("Seed 5", svg)
                self.assertIn("prefers-reduced-motion", svg)
                self.assertLess(len(svg), 400_000, f"{name} is too big for a profile picture")


if __name__ == "__main__":
    unittest.main()
