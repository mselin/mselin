"""Tests for games_table.py, without the network: python3 -m unittest discover -s .github/scripts"""

import unittest

import games_table

G = [
    {"name": "Game", "summary": "A game.", "play": "https://p/", "source": "https://s/", "tags": []},
    {"name": "Other", "summary": "Another.", "play": "https://q/", "source": "https://t/", "tags": []},
]
README = "\n".join([
    "| What | Details |",
    "|---|---|",
    "| **SID** | A chip |",
    "| **[Game](https://p/)** | Old words. [Play it](https://p/) |",
    "",
    "After the table.",
])


class GamesTable(unittest.TestCase):
    def test_a_row_is_rewritten_and_a_missing_game_added_after_it(self):
        out = games_table.rewrite(README, G).split("\n")
        self.assertEqual(out[3], "| **[Game](https://p/)** | A game. [Play it](https://p/) · [Source](https://s/) |")
        self.assertEqual(out[4], "| **[Other](https://q/)** | Another. [Play it](https://q/) · [Source](https://t/) |")
        self.assertEqual(out[2], "| **SID** | A chip |", "other rows are left alone")
        self.assertEqual(out[6], "After the table.")

    def test_rewriting_twice_changes_nothing(self):
        once = games_table.rewrite(README, G)
        self.assertEqual(once, games_table.rewrite(once, G))

    def test_a_game_without_play_links_to_its_source(self):
        app = {"name": "App", "summary": "An app.", "source": "https://u/", "tags": []}
        want = "| **[App](https://u/)** | An app. [Source](https://u/) |"
        added = games_table.rewrite(README, G + [app])
        self.assertEqual(added.split("\n")[5], want, "added after the other games")
        self.assertEqual(added, games_table.rewrite(added, G + [app]), "and found again by its source link")
        stale = added.replace("An app.", "Old words.")
        self.assertEqual(games_table.rewrite(stale, G + [app]), added)

    def test_no_table_to_add_to_is_an_error(self):
        with self.assertRaises(ValueError):
            games_table.rewrite("Just words.", G)


if __name__ == "__main__":
    unittest.main()
