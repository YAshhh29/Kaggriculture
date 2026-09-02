"""Typed macro decisions for a residual Kaggriculture policy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class LaborDecision(IntEnum):
    KEEP = 0
    REDUCE_ONE = 1
    ADD_ONE = 2


class LandDecision(IntEnum):
    KEEP = 0
    BUY_NEXT = 1


class CropDecision(IntEnum):
    KEEP = 0
    DEMAND_BEST = 1
    WHEAT = 2
    STRAWBERRY = 3
    MELON = 4


class ServiceDecision(IntEnum):
    KEEP = 0
    SPARSE = 1
    FULL = 2
    ABANDON_LOW_VALUE = 3


class MarketDecision(IntEnum):
    KEEP = 0
    PRESERVE_CASH = 1
    PACE_SALES = 2
    LIQUIDATE = 3


class RecoveryDecision(IntEnum):
    KEEP = 0
    REPAIR_STATE_DRIFT = 1


ACTION_HEAD_SIZES = (
    len(LaborDecision),
    len(LandDecision),
    len(CropDecision),
    len(ServiceDecision),
    len(MarketDecision),
    len(RecoveryDecision),
)


@dataclass(frozen=True)
class ResidualAction:
    """One factored correction to the trusted calendar policy."""

    labor: LaborDecision = LaborDecision.KEEP
    land: LandDecision = LandDecision.KEEP
    crop: CropDecision = CropDecision.KEEP
    service: ServiceDecision = ServiceDecision.KEEP
    market: MarketDecision = MarketDecision.KEEP
    recovery: RecoveryDecision = RecoveryDecision.KEEP

    @property
    def is_keep_calendar(self) -> bool:
        return self == KEEP_CALENDAR

    def head_indices(self) -> tuple[int, ...]:
        """Return one categorical index for each policy head."""
        return tuple(
            int(value)
            for value in (
                self.labor,
                self.land,
                self.crop,
                self.service,
                self.market,
                self.recovery,
            )
        )


KEEP_CALENDAR = ResidualAction()