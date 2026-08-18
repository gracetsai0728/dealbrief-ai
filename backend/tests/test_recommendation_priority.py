import unittest
from datetime import date
from types import SimpleNamespace

from app.services.recommendation_priority import calculate_priority_decisions


def product(product_id, status="active"):
    return SimpleNamespace(id=product_id, status=status)


def subscription(
    product_id,
    start,
    end,
    status,
    seats,
):
    return SimpleNamespace(
        product_id=product_id,
        subscription_start_date=start,
        subscription_end_date=end,
        subscription_status=status,
        licensed_seats=seats,
    )


class RecommendationPriorityTests(unittest.TestCase):
    as_of = date(2026, 8, 17)

    def test_product_gap_and_near_renewal_create_high_cross_sell_priority(self):
        decisions = calculate_priority_decisions(
            [product("crm"), product("analytics")],
            [
                subscription(
                    "crm",
                    date(2026, 1, 1),
                    date(2026, 10, 1),
                    "active",
                    1200,
                )
            ],
            self.as_of,
        )

        self.assertEqual(decisions["crossSell"].score, 6)
        self.assertEqual(decisions["crossSell"].priority, "high")

    def test_all_products_owned_make_cross_sell_low(self):
        decisions = calculate_priority_decisions(
            [product("crm"), product("analytics")],
            [
                subscription(
                    "crm",
                    date(2026, 1, 1),
                    date(2027, 1, 1),
                    "active",
                    400,
                ),
                subscription(
                    "analytics",
                    date(2026, 2, 1),
                    date(2027, 2, 1),
                    "active",
                    300,
                ),
            ],
            self.as_of,
        )

        self.assertEqual(decisions["crossSell"].priority, "low")

    def test_observed_growth_can_create_high_upsell_priority(self):
        decisions = calculate_priority_decisions(
            [product("crm")],
            [
                subscription(
                    "crm",
                    date(2025, 1, 1),
                    date(2025, 12, 31),
                    "expired",
                    800,
                ),
                subscription(
                    "crm",
                    date(2026, 1, 1),
                    date(2026, 10, 1),
                    "active",
                    1200,
                ),
            ],
            self.as_of,
        )

        self.assertEqual(decisions["upsell"].score, 6)
        self.assertEqual(decisions["upsell"].priority, "high")

    def test_large_account_without_growth_is_capped_at_medium_upsell(self):
        decisions = calculate_priority_decisions(
            [product("crm")],
            [
                subscription(
                    "crm",
                    date(2025, 1, 1),
                    date(2025, 12, 31),
                    "expired",
                    1200,
                ),
                subscription(
                    "crm",
                    date(2026, 1, 1),
                    date(2026, 10, 1),
                    "active",
                    1200,
                ),
            ],
            self.as_of,
        )

        self.assertEqual(decisions["upsell"].score, 4)
        self.assertEqual(decisions["upsell"].priority, "medium")

    def test_recent_meaningful_lapse_creates_high_winback_priority(self):
        decisions = calculate_priority_decisions(
            [product("crm")],
            [
                subscription(
                    "crm",
                    date(2025, 7, 1),
                    date(2026, 7, 31),
                    "canceled",
                    600,
                )
            ],
            self.as_of,
        )

        self.assertEqual(decisions["winback"].score, 5)
        self.assertEqual(decisions["winback"].priority, "high")
        self.assertEqual(decisions["renewal"].priority, "low")

    def test_no_lapsed_product_makes_winback_low(self):
        decisions = calculate_priority_decisions(
            [product("crm")],
            [
                subscription(
                    "crm",
                    date(2026, 1, 1),
                    date(2027, 1, 1),
                    "active",
                    500,
                )
            ],
            self.as_of,
        )

        self.assertEqual(decisions["winback"].score, 0)
        self.assertEqual(decisions["winback"].priority, "low")


if __name__ == "__main__":
    unittest.main()
