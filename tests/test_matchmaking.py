from __future__ import annotations

import unittest
from unittest.mock import patch

from simplescript import (
    Player,
    choose_anchor_window,
    choose_best_window,
    split_balanced_teams,
    split_sequential_teams,
)


def player_with_mmr(mmr: int, waiting_time: int = 0) -> Player:
    player = Player(mmr=mmr, waiting_time=waiting_time)
    return player


class MatchmakingTests(unittest.TestCase):
    def test_choose_best_window_prefers_tightest_group(self) -> None:
        players = [
            player_with_mmr(1000),
            player_with_mmr(1400),
            player_with_mmr(1800),
            player_with_mmr(2200),
            player_with_mmr(2600),
            player_with_mmr(3000),
            player_with_mmr(3010),
            player_with_mmr(3020),
            player_with_mmr(3030),
            player_with_mmr(3040),
            player_with_mmr(3050),
            player_with_mmr(3060),
        ]

        start, window = choose_best_window(players, lobby_size=10)

        self.assertEqual(start, 2)
        self.assertEqual([player.mmr for player in window], [1800, 2200, 2600, 3000, 3010, 3020, 3030, 3040, 3050, 3060])

    def test_split_balanced_teams_minimizes_mmr_gap(self) -> None:
        window = [
            player_with_mmr(2800),
            player_with_mmr(2900),
            player_with_mmr(3000),
            player_with_mmr(3100),
            player_with_mmr(3200),
            player_with_mmr(3300),
            player_with_mmr(3400),
            player_with_mmr(3500),
            player_with_mmr(3600),
            player_with_mmr(3700),
        ]

        radiant, dire = split_balanced_teams(window)
        gap = abs(sum(player.mmr for player in radiant) - sum(player.mmr for player in dire))

        self.assertEqual(len(radiant), 5)
        self.assertEqual(len(dire), 5)
        self.assertEqual(gap, 100)

    def test_choose_anchor_window_returns_anchor_and_nearest_players(self) -> None:
        players = [
            player_with_mmr(1000),
            player_with_mmr(1400),
            player_with_mmr(1800),
            player_with_mmr(2200),
            player_with_mmr(2600),
            player_with_mmr(3000),
            player_with_mmr(3010),
            player_with_mmr(3020),
            player_with_mmr(3030),
            player_with_mmr(3040),
            player_with_mmr(3500),
            player_with_mmr(4100),
        ]

        with patch("simplescript.random.randrange", return_value=5):
            _, window = choose_anchor_window(players, lobby_size=10)

        self.assertEqual(
            [player.mmr for player in sorted(window, key=lambda player: player.mmr)],
            [1800, 2200, 2600, 3000, 3010, 3020, 3030, 3040, 3500, 4100],
        )

    def test_split_sequential_teams_preserves_sorted_halves(self) -> None:
        window = [
            player_with_mmr(2800),
            player_with_mmr(2900),
            player_with_mmr(3000),
            player_with_mmr(3100),
            player_with_mmr(3200),
            player_with_mmr(3300),
            player_with_mmr(3400),
            player_with_mmr(3500),
            player_with_mmr(3600),
            player_with_mmr(3700),
        ]

        radiant, dire = split_sequential_teams(window)

        self.assertEqual([player.mmr for player in radiant], [2800, 2900, 3000, 3100, 3200])
        self.assertEqual([player.mmr for player in dire], [3300, 3400, 3500, 3600, 3700])


if __name__ == "__main__":
    unittest.main()
