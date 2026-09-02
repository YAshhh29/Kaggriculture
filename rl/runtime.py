"""Fail-closed bridge from a residual policy to a Kaggle agent."""

from __future__ import annotations

from typing import Any, Callable, Protocol

from agents.experimental_distilled_calendar_agent import decide as calendar
from rl.action_space import ResidualAction
from rl.features import encode_state
from rl.policy import ResidualPolicy


AgentAction = dict[str, Any]
Baseline = Callable[[dict[str, Any]], AgentAction]


class UnsupportedResidualAction(RuntimeError):
    """Raised before an unimplemented learned action can reach Kaggle."""


class ResidualExecutor(Protocol):
    def apply(
        self,
        observation: dict[str, Any],
        baseline_action: AgentAction,
        residual_action: ResidualAction,
    ) -> AgentAction:
        """Safely translate one macro correction into primitive actions."""


def clone_action(action: AgentAction) -> AgentAction:
    return {
        "farmer": list(action.get("farmer", ["PASS"])),
        "hands": [list(item) for item in action.get("hands", [])],
        "market": [list(item) for item in action.get("market", [])],
    }


class KeepOnlyExecutor:
    """Phase-zero executor that permits no behavioral drift."""

    def apply(
        self,
        observation: dict[str, Any],
        baseline_action: AgentAction,
        residual_action: ResidualAction,
    ) -> AgentAction:
        del observation
        if not residual_action.is_keep_calendar:
            raise UnsupportedResidualAction(
                "Residual execution is not implemented for "
                f"{residual_action!r}"
            )
        return clone_action(baseline_action)


def build_residual_agent(
    policy: ResidualPolicy,
    *,
    baseline: Baseline = calendar,
    executor: ResidualExecutor | None = None,
) -> Baseline:
    """Create a Kaggle callable while preserving deterministic safety."""
    selected_executor = executor or KeepOnlyExecutor()

    def agent(observation: dict[str, Any]) -> AgentAction:
        baseline_action = baseline(observation)
        state = encode_state(observation, baseline_action)
        residual_action = policy.select_action(state)
        return selected_executor.apply(
            observation,
            baseline_action,
            residual_action,
        )

    return agent