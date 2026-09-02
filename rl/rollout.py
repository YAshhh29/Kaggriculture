"""Thin, testable adapter around the official Kaggriculture simulator."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from benchmark import load_agent_callable


Agent = Callable[[dict[str, Any]], dict[str, Any]]
EnvironmentFactory = Callable[..., Any]


@dataclass(frozen=True)
class EpisodeResult:
    seed: int
    candidate_player: int
    candidate_reward: float
    opponent_reward: float
    statuses: tuple[str, str]
    records: int
    elapsed_seconds: float

    @property
    def result(self) -> str:
        if self.candidate_reward > self.opponent_reward:
            return "win"
        if self.candidate_reward < self.opponent_reward:
            return "loss"
        return "tie"


@dataclass(frozen=True)
class PairedResult:
    seed: int
    episodes: tuple[EpisodeResult, EpisodeResult]

    @property
    def wins(self) -> int:
        return sum(episode.result == "win" for episode in self.episodes)

    @property
    def losses(self) -> int:
        return sum(episode.result == "loss" for episode in self.episodes)

    @property
    def ties(self) -> int:
        return sum(episode.result == "tie" for episode in self.episodes)

    @property
    def mean_margin(self) -> float:
        margins = [
            episode.candidate_reward - episode.opponent_reward
            for episode in self.episodes
        ]
        return sum(margins) / len(margins)

    def as_json(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "wins": self.wins,
            "losses": self.losses,
            "ties": self.ties,
            "mean_margin": self.mean_margin,
            "episodes": [
                {**asdict(episode), "result": episode.result}
                for episode in self.episodes
            ],
        }


def _official_factory() -> EnvironmentFactory:
    from kaggle_environments import make

    return make


def run_episode(
    candidate: Agent,
    opponent: Agent | str,
    *,
    seed: int,
    candidate_player: int,
    episode_steps: int = 720,
    make_environment: EnvironmentFactory | None = None,
) -> EpisodeResult:
    """Run one paired evaluation episode using deployable observations."""
    if candidate_player not in (0, 1):
        raise ValueError("candidate_player must be 0 or 1")
    factory = make_environment or _official_factory()
    environment = factory(
        "kaggriculture",
        configuration={"episodeSteps": episode_steps, "seed": seed},
        debug=False,
    )
    agents: list[Any] = [candidate, opponent]
    if candidate_player == 1:
        agents.reverse()
    started = perf_counter()
    environment.run(agents)
    elapsed = perf_counter() - started
    if not environment.steps or len(environment.steps[-1]) != 2:
        raise RuntimeError("Episode has no valid final player states")
    final = environment.steps[-1]
    statuses = (str(final[0].status), str(final[1].status))
    if statuses != ("DONE", "DONE"):
        raise RuntimeError(f"Episode did not finish successfully: {statuses}")
    rewards = (float(final[0].reward), float(final[1].reward))
    return EpisodeResult(
        seed=seed,
        candidate_player=candidate_player,
        candidate_reward=rewards[candidate_player],
        opponent_reward=rewards[1 - candidate_player],
        statuses=statuses,
        records=len(environment.steps),
        elapsed_seconds=elapsed,
    )


def run_paired(
    candidate: Agent,
    opponent: Agent | str,
    *,
    seed: int,
    episode_steps: int = 720,
    make_environment: EnvironmentFactory | None = None,
) -> PairedResult:
    """Run the same seed with the candidate in both player positions."""
    episodes = tuple(
        run_episode(
            candidate,
            opponent,
            seed=seed,
            candidate_player=player,
            episode_steps=episode_steps,
            make_environment=make_environment,
        )
        for player in (0, 1)
    )
    return PairedResult(seed=seed, episodes=episodes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("opponent", type=Path)
    parser.add_argument("--seed", type=int, default=50_000)
    parser.add_argument("--player", type=int, choices=(0, 1))
    args = parser.parse_args()
    candidate = load_agent_callable(args.candidate.resolve())
    opponent = load_agent_callable(args.opponent.resolve())
    if args.player is None:
        print(
            json.dumps(
                run_paired(candidate, opponent, seed=args.seed).as_json(),
                indent=2,
            )
        )
        return
    result = run_episode(
        candidate,
        opponent,
        seed=args.seed,
        candidate_player=args.player,
    )
    print(json.dumps({**asdict(result), "result": result.result}, indent=2))


if __name__ == "__main__":
    main()