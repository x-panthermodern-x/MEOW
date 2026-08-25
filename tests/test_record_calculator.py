import unittest
from datetime import date

from programs.meow_record_calc import (
    CashFlowSchedule,
    Manufacturing,
    ReleaseCosts,
    SalesPlan,
    ShopifyFees,
    add_months,
    allocate_integer_total,
    build_cashflow_timeline,
    compute_release_pnl,
)


class RecordCalculatorTests(unittest.TestCase):
    def setUp(self):
        self.manufacturing = Manufacturing(
            units=560,
            manufacturing_total=4294.05,
        )
        self.costs = ReleaseCosts(
            marketing=5000,
            mastering=2000,
            artwork=1000,
        )
        self.fees = ShopifyFees(rate=0.029, fixed_per_order=0.30)
        self.schedule = CashFlowSchedule(release_date=date(2026, 11, 1))

    def test_default_profit_and_loss(self):
        result = compute_release_pnl(
            self.manufacturing,
            self.costs,
            SalesPlan(),
            self.fees,
        )

        self.assertEqual(result["units_sold"], 560)
        self.assertEqual(result["est_orders"], 560)
        self.assertAlmostEqual(result["gross_revenue"], 19600.00)
        self.assertAlmostEqual(result["processing_fees"], 736.40)
        self.assertAlmostEqual(result["total_cost_basis"], 12294.05)
        self.assertAlmostEqual(result["net_profit_pre_tax"], 6569.55)

        break_even = result["break_even_price_including_processing"]
        recovered = (
            break_even * result["units_sold"] * (1 - self.fees.rate)
            - result["est_orders"] * self.fees.fixed_per_order
        )
        self.assertAlmostEqual(recovered, result["total_cost_basis"])

    def test_cashflow_reconciles_to_profit_and_loss(self):
        scenarios = (
            SalesPlan(sell_through=1.0, avg_units_per_order=1.0),
            SalesPlan(sell_through=0.75, avg_units_per_order=1.7),
            SalesPlan(sell_through=0.0, avg_units_per_order=1.0),
        )

        for sales in scenarios:
            with self.subTest(sales=sales):
                result = compute_release_pnl(
                    self.manufacturing,
                    self.costs,
                    sales,
                    self.fees,
                )
                rows = build_cashflow_timeline(
                    self.manufacturing,
                    self.costs,
                    sales,
                    self.fees,
                    self.schedule,
                )
                self.assertAlmostEqual(
                    rows[-1]["cumulative"],
                    result["net_profit_pre_tax"],
                )

    def test_integer_allocation_has_no_rounding_drift(self):
        allocation = allocate_integer_total(560, [0.4, 0.3, 0.2, 0.1])
        self.assertEqual(sum(allocation), 560)
        self.assertTrue(all(value >= 0 for value in allocation))

    def test_month_add_clamps_to_month_end(self):
        self.assertEqual(add_months(date(2024, 1, 31), 1), date(2024, 2, 29))

    def test_invalid_inputs_are_rejected(self):
        invalid_cases = (
            (Manufacturing, {"units": 0}),
            (SalesPlan, {"sell_through": 1.01}),
            (SalesPlan, {"avg_units_per_order": 0.5}),
            (SalesPlan, {"months_to_sell": 0}),
            (ShopifyFees, {"rate": 1.0}),
            (ReleaseCosts, {"marketing": -1}),
        )
        for constructor, arguments in invalid_cases:
            with self.subTest(constructor=constructor.__name__):
                with self.assertRaises(ValueError):
                    constructor(**arguments)


if __name__ == "__main__":
    unittest.main()
