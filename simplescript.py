#!/usr/bin/env python3
"""Simple Dota 2 matchmaking simulation."""

from __future__ import annotations

import argparse
import itertools
import random
from dataclasses import dataclass, field

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - plotting is optional
    plt = None


PLAYER_COUNTER = 0
MATCH_COUNTER = 0


def next_player_index() -> int:
    global PLAYER_COUNTER
    PLAYER_COUNTER += 1
    return PLAYER_COUNTER


def next_match_id() -> int:
    global MATCH_COUNTER
    MATCH_COUNTER += 1
    return MATCH_COUNTER


@dataclass
class Player:
    """Queue player with a sampled MMR and waiting time."""

    mmr: int = field(default_factory=lambda: round(random.gauss(0, 1) * 1000, -1) + 3000)
    waiting_time: int = 0
    index: int = field(default_factory=next_player_index)


@dataclass
class Match:
    """10-player match split into two teams."""

    players: list[Player]
    team_radiant: list[Player]
    team_dire: list[Player]
    algorithm: str
    match_id: int = field(default_factory=next_match_id)

    @property
    def lobby_spread(self) -> int:
        mmrs = [player.mmr for player in self.players]
        return max(mmrs) - min(mmrs)

    @property
    def mmr_gap(self) -> int:
        return abs(sum(player.mmr for player in self.team_radiant) - sum(player.mmr for player in self.team_dire))

    def __str__(self) -> str:
        return "\n".join(
            [
                f"{'match id':>20s} : {self.match_id}",
                f"{'algorithm':>20s} : {self.algorithm}",
                f"{'queue spread':>20s} : {self.lobby_spread}",
                f"{'team mmr gap':>20s} : {self.mmr_gap}",
                f"{'radiant mmr':>20s} : {','.join(str(player.mmr) for player in self.team_radiant)}",
                f"{'dire mmr':>20s} : {','.join(str(player.mmr) for player in self.team_dire)}",
                f"{'player id':>20s} : {','.join(str(player.index) for player in self.players)}",
            ]
        )


class Matchmaker:
    def __init__(self, num_players: int = 5000) -> None:
        self.players = [Player() for _ in range(num_players)]
        self.sort()

    def sort(self) -> None:
        self.players.sort(key=lambda player: (player.mmr, player.index))

    def get_mmr(self) -> list[int]:
        return [player.mmr for player in self.players]

    def plot_histogram(self, bins: int = 30) -> None:
        if plt is None:
            raise RuntimeError("matplotlib is not installed.")
        plt.hist(self.get_mmr(), bins=bins)
        plt.show()


def score_window(window: list[Player], wait_weight: int = 25) -> tuple[float, int, int]:
    spread = max(player.mmr for player in window) - min(player.mmr for player in window)
    average_wait = sum(player.waiting_time for player in window) / len(window)
    highest_wait = max(player.waiting_time for player in window)
    return (spread - (average_wait * wait_weight), spread, -highest_wait)


def choose_best_window(players: list[Player], lobby_size: int = 10) -> tuple[int, list[Player]]:
    if len(players) < lobby_size:
        raise ValueError("Not enough players to form a lobby.")

    best_index = 0
    best_window = players[:lobby_size]
    best_score = score_window(best_window)

    for start in range(1, len(players) - lobby_size + 1):
        window = players[start : start + lobby_size]
        current_score = score_window(window)
        if current_score < best_score:
            best_index = start
            best_window = window
            best_score = current_score

    return best_index, list(best_window)


def split_balanced_teams(window: list[Player], team_size: int = 5) -> tuple[list[Player], list[Player]]:
    if len(window) != team_size * 2:
        raise ValueError("Balanced split expects exactly 10 players.")

    total_mmr = sum(player.mmr for player in window)
    best_team: tuple[Player, ...] | None = None
    smallest_gap: int | None = None

    for radiant_team in itertools.combinations(window, team_size):
        radiant_mmr = sum(player.mmr for player in radiant_team)
        gap = abs(total_mmr - 2 * radiant_mmr)
        if smallest_gap is None or gap < smallest_gap:
            best_team = radiant_team
            smallest_gap = gap
            if gap == 0:
                break

    assert best_team is not None
    radiant_ids = {player.index for player in best_team}
    dire_team = [player for player in window if player.index not in radiant_ids]
    return sorted(best_team, key=lambda player: player.mmr), sorted(dire_team, key=lambda player: player.mmr)


def split_sequential_teams(window: list[Player], team_size: int = 5) -> tuple[list[Player], list[Player]]:
    if len(window) != team_size * 2:
        raise ValueError("Sequential split expects exactly 10 players.")
    ordered_window = sorted(window, key=lambda player: player.mmr)
    return ordered_window[:team_size], ordered_window[team_size:]


def choose_anchor_window(players: list[Player], lobby_size: int = 10) -> tuple[int, list[Player]]:
    if len(players) < lobby_size:
        raise ValueError("Not enough players to form a lobby.")

    anchor_index = random.randrange(len(players))
    anchor_player = players[anchor_index]
    ranked = sorted(
        enumerate(players),
        key=lambda item: (abs(item[1].mmr - anchor_player.mmr), abs(item[0] - anchor_index), item[0]),
    )
    selected_indices = sorted(index for index, _ in ranked[:lobby_size])
    selected_players = [players[index] for index in selected_indices]
    return selected_indices[0], selected_players


def remove_players(players: list[Player], selected_players: list[Player]) -> None:
    selected_ids = {player.index for player in selected_players}
    players[:] = [player for player in players if player.index not in selected_ids]


def form_balanced_window_match(players: list[Player], lobby_size: int = 10) -> Match:
    start, window = choose_best_window(players, lobby_size=lobby_size)
    del players[start : start + lobby_size]
    radiant, dire = split_balanced_teams(window, team_size=lobby_size // 2)
    return Match(
        players=sorted(window, key=lambda player: player.mmr),
        team_radiant=radiant,
        team_dire=dire,
        algorithm="balanced-window",
    )


def form_anchor_nearest_match(players: list[Player], lobby_size: int = 10) -> Match:
    _, window = choose_anchor_window(players, lobby_size=lobby_size)
    remove_players(players, window)
    ordered_window = sorted(window, key=lambda player: player.mmr)
    radiant, dire = split_sequential_teams(ordered_window, team_size=lobby_size // 2)
    return Match(
        players=ordered_window,
        team_radiant=radiant,
        team_dire=dire,
        algorithm="anchor-nearest",
    )


def age_queue(players: list[Player], amount: int = 1) -> None:
    for player in players:
        player.waiting_time += amount


def simulate(num_players: int, algorithm: str = "balanced-window", plot_histogram: bool = False) -> list[Match]:
    matchmaker = Matchmaker(num_players)
    if plot_histogram:
        matchmaker.plot_histogram()

    matches: list[Match] = []
    while len(matchmaker.players) >= 10:
        age_queue(matchmaker.players)
        if algorithm == "balanced-window":
            match = form_balanced_window_match(matchmaker.players)
        elif algorithm == "anchor-nearest":
            match = form_anchor_nearest_match(matchmaker.players)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        matches.append(match)
        print(match)
        print("")

    print(f"finished matching players.. remaining players in queue:{len(matchmaker.players)}")
    return matches


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate Dota 2 matchmaking with multiple algorithms.")
    parser.add_argument(
        "--algorithm",
        choices=["balanced-window", "anchor-nearest"],
        default="balanced-window",
        help="Match formation strategy to use.",
    )
    parser.add_argument("--players", type=int, default=50, help="Number of queued players to simulate.")
    parser.add_argument("--plot-histogram", action="store_true", help="Plot the initial MMR distribution.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    simulate(args.players, algorithm=args.algorithm, plot_histogram=args.plot_histogram)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
