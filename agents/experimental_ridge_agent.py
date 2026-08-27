"""Development-only ridge market policy wrapped around frozen v9 controls."""

from __future__ import annotations

from typing import Any

from main import decide


TRAINED_MINIMUM_PRICE = 28
TRAINED_MAXIMUM_PRICE = 40
MINIMUM_PREDICTED_SELL_ADVANTAGE = 8.0
MAXIMUM_WHEAT_HOLDINGS = 72
WHEAT_LIQUIDATION_DAY = 25

RIDGE_INTERCEPT = -25.99166666666666
RIDGE_MEANS = {
    "day": 12.833333333333334,
    "hour": 5.016666666666667,
    "money": 3992.6916666666666,
    "wheat_seeds": 0.8416666666666667,
    "shed_wheat": 21.266666666666666,
    "carried_wheat": 0.36666666666666664,
    "planted_wheat": 4.991666666666666,
    "wheat_market_price": 34.3,
    "wheat_market_inventory": 9905.141666666666,
}
RIDGE_SCALES = {
    "day": 6.72722495205531,
    "hour": 5.860863607201776,
    "money": 1402.482654651109,
    "wheat_seeds": 1.4719365550940782,
    "shed_wheat": 14.993183636424773,
    "carried_wheat": 2.1906366400863675,
    "planted_wheat": 1.6201637434393956,
    "wheat_market_price": 3.446254004954752,
    "wheat_market_inventory": 66.87566770175499,
}
RIDGE_COEFFICIENTS = {
    "day": 7.858692342793088,
    "hour": 0.4192631916693973,
    "money": 1.6767870753947043,
    "wheat_seeds": -9.83476694871775,
    "shed_wheat": 6.344723609304555,
    "carried_wheat": 4.314059203489884,
    "planted_wheat": 7.632607961464206,
    "wheat_market_price": 6.50129954651904,
    "wheat_market_inventory": -4.72876567608679,
}


def _market_features(observation: dict[str, Any]) -> dict[str, float]:
    player = int(observation["player"])
    farm = observation["farms"][player]
    private = observation["private"]
    return {
        "day": float(observation["day"]),
        "hour": float(observation["hour"]),
        "money": float(farm["money"]),
        "wheat_seeds": float(
            private.get("seeds", {}).get("WHEAT", 0)
        ),
        "shed_wheat": float(
            private.get("shed", {}).get("WHEAT", 0)
        ),
        "carried_wheat": float(
            sum(
                inventory.get("WHEAT", 0)
                for inventory in private.get("inventories", [])
            )
        ),
        "planted_wheat": float(
            sum(
                isinstance(tile, dict)
                and tile.get("kind") == "PLANT"
                and tile.get("crop") == "WHEAT"
                for row in farm["tiles"]
                for tile in row
            )
        ),
        "wheat_market_price": float(
            observation["market"].get("prices", {}).get("WHEAT", 0)
        ),
        "wheat_market_inventory": float(
            observation["market"].get("inventory", {}).get("WHEAT", 0)
        ),
    }


def _predicted_sell_advantage(observation: dict[str, Any]) -> float:
    features = _market_features(observation)
    prediction = RIDGE_INTERCEPT
    for feature, coefficient in RIDGE_COEFFICIENTS.items():
        standardized = (
            features[feature] - RIDGE_MEANS[feature]
        ) / RIDGE_SCALES[feature]
        prediction += coefficient * standardized
    return prediction


def _is_wheat_sale(order: Any) -> bool:
    return (
        isinstance(order, list)
        and len(order) >= 3
        and order[0] == "SELL"
        and order[1] == "WHEAT"
    )


def _apply_learned_market_choice(
    observation: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    day = int(observation["day"])
    private = observation["private"]
    shed_wheat = int(private.get("shed", {}).get("WHEAT", 0))
    price = int(
        observation["market"].get("prices", {}).get("WHEAT", 0)
    )
    if (
        shed_wheat <= 0
        or shed_wheat >= MAXIMUM_WHEAT_HOLDINGS
        or day >= WHEAT_LIQUIDATION_DAY
        or not TRAINED_MINIMUM_PRICE <= price <= TRAINED_MAXIMUM_PRICE
    ):
        return decision

    retained = [
        order
        for order in decision.get("market", [])
        if not _is_wheat_sale(order)
    ]
    if (
        _predicted_sell_advantage(observation)
        > MINIMUM_PREDICTED_SELL_ADVANTAGE
    ):
        decision["market"] = [
            ["SELL", "WHEAT", shed_wheat],
            *retained,
        ]
    else:
        decision["market"] = retained
    return decision


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Apply the learned market choice inside frozen v9 safety controls."""
    return _apply_learned_market_choice(observation, decide(observation))