"""Policy interface used by training and deployment adapters."""

from __future__ import annotations

from typing import Protocol

from rl.action_space import KEEP_CALENDAR, ResidualAction
from rl.features import EncodedState


class ResidualPolicy(Protocol):
    def select_action(self, state: EncodedState) -> ResidualAction:
        """Choose a correction to the trusted calendar."""


class KeepCalendarPolicy:
    """Reference policy and mandatory training baseline."""

    def select_action(self, state: EncodedState) -> ResidualAction:
        del state
        return KEEP_CALENDAR