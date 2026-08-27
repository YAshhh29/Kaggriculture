import unittest
from unittest.mock import patch

from agents.experimental_wheat_trader_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalWheatTraderAgentTests(unittest.TestCase):
    def test_enables_bounded_wheat_trade_band(self) -> None:
        with patch(
            "agents.experimental_wheat_trader_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertEqual(premium.call_args.kwargs["wheat_trade_target"], 48)
        self.assertEqual(
            premium.call_args.kwargs["wheat_trade_buy_price"], 34
        )
        self.assertEqual(
            premium.call_args.kwargs["wheat_trade_sell_price"], 40
        )


if __name__ == "__main__":
    unittest.main()
