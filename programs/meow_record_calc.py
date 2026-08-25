
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional
import math

# ---------- Utils ----------

def money(x: float) -> str:
    sign = "-" if x < 0 else ""
    x = abs(x)
    return f"{sign}${x:,.2f}"

def add_months(d: date, months: int) -> date:
    # minimal month add (no external deps)
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    # clamp day to end of month
    mdays = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day = min(d.day, mdays[m - 1])
    return date(y, m, day)

# ---------- Core Model ----------

@dataclass
class ShopifyFees:
    rate: float = 0.029       # 2.9%
    fixed_per_order: float = 0.30

    def __post_init__(self):
        if not 0 <= self.rate < 1:
            raise ValueError("Processing-fee rate must be between 0 and 1.")
        if self.fixed_per_order < 0:
            raise ValueError("Fixed processing fee cannot be negative.")

@dataclass
class ReleaseCosts:
    marketing: float = 5000.0
    mastering: float = 2000.0
    artwork: float = 1000.0

    def __post_init__(self):
        if min(self.marketing, self.mastering, self.artwork) < 0:
            raise ValueError("Release costs cannot be negative.")

    @property
    def total(self) -> float:
        return self.marketing + self.mastering + self.artwork

@dataclass
class Manufacturing:
    units: int = 560
    manufacturing_total: float = 4294.05  # your AtoZ subtotal (includes inbound freight + delivery)

    def __post_init__(self):
        if self.units <= 0:
            raise ValueError("Units pressed must be greater than zero.")
        if self.manufacturing_total < 0:
            raise ValueError("Manufacturing total cannot be negative.")

    @property
    def cost_per_unit(self) -> float:
        return self.manufacturing_total / self.units

@dataclass
class SalesPlan:
    unit_price: float = 35.0

    # Order model:
    # For conservative planning, assume 1 unit per order.
    # You can increase avg_units_per_order (e.g. 1.15) to reduce $0.30 fee drag.
    avg_units_per_order: float = 1.0

    # Sell-through assumptions
    sell_through: float = 1.00      # 1.0 = sell all units
    months_to_sell: int = 8         # spread sales across N months after release

    # Distribution of sales across months after release.
    # If None, uses a simple front-loaded curve.
    monthly_weights: Optional[List[float]] = None

    def __post_init__(self):
        if self.unit_price < 0:
            raise ValueError("Unit price cannot be negative.")
        if self.avg_units_per_order < 1:
            raise ValueError("Average units per order must be at least 1.")
        if not 0 <= self.sell_through <= 1:
            raise ValueError("Sell-through must be between 0 and 1.")
        if self.months_to_sell < 1:
            raise ValueError("Months to sell through must be at least 1.")

@dataclass
class CashFlowSchedule:
    """
    Timeline assumptions. All dates are relative to release_date.

    Common pattern:
      - Manufacturing deposit earlier
      - Manufacturing balance closer to ship
      - Freight/delivery at arrival
      - Mastering/art earlier in production cycle
      - Marketing spread around release
      - Sales start at release_date
    """
    release_date: date

    # Manufacturing payment timing
    mfg_deposit_pct: float = 0.50
    mfg_deposit_months_before_release: int = 4
    mfg_balance_months_before_release: int = 2

    # Extra inbound already included in manufacturing_total for your receipt;
    # if you ever split it out, you can add it here as separate cash outflows.
    # For now we keep it simple.

    # Fixed release costs timing (months relative to release)
    mastering_months_before_release: int = 3
    artwork_months_before_release: int = 3

    # Marketing spending profile (fractions must sum to 1.0)
    # Example: 25% one month before release, 50% on release month, 25% one month after.
    marketing_profile: Optional[Dict[int, float]] = None

    def __post_init__(self):
        if not 0 <= self.mfg_deposit_pct <= 1:
            raise ValueError("Manufacturing deposit percentage must be between 0 and 1.")
        timing_values = (
            self.mfg_deposit_months_before_release,
            self.mfg_balance_months_before_release,
            self.mastering_months_before_release,
            self.artwork_months_before_release,
        )
        if min(timing_values) < 0:
            raise ValueError("Months-before-release values cannot be negative.")
        if self.marketing_profile is None:
            self.marketing_profile = {-1: 0.25, 0: 0.50, 1: 0.25}
        if not self.marketing_profile:
            raise ValueError("Marketing profile cannot be empty.")
        if any(fraction < 0 for fraction in self.marketing_profile.values()):
            raise ValueError("Marketing-profile fractions cannot be negative.")
        s = sum(self.marketing_profile.values())
        if not (0.999 <= s <= 1.001):
            raise ValueError(f"marketing_profile fractions must sum to 1.0, got {s}")

# ---------- Calculators ----------

def default_sales_weights(months: int) -> List[float]:
    """
    Simple front-loaded curve:
      month1 heavier, then tapers.
    """
    if months <= 0:
        return []
    raw = []
    for i in range(months):
        # decay curve
        raw.append(1.0 / (1.0 + i * 0.6))
    total = sum(raw)
    return [x / total for x in raw]


def estimate_orders(units_sold: int, avg_units_per_order: float) -> int:
    if units_sold <= 0:
        return 0
    return math.ceil(units_sold / avg_units_per_order)


def allocate_integer_total(total: int, weights: List[float]) -> List[int]:
    """Allocate an integer total proportionally without rounding drift."""
    if total < 0:
        raise ValueError("Allocation total cannot be negative.")
    if not weights:
        if total == 0:
            return []
        raise ValueError("Cannot allocate a positive total without weights.")
    if any(weight < 0 for weight in weights):
        raise ValueError("Allocation weights cannot be negative.")

    weight_total = sum(weights)
    if weight_total <= 0:
        if total == 0:
            return [0] * len(weights)
        raise ValueError("Allocation weights must have a positive sum.")

    exact = [total * weight / weight_total for weight in weights]
    allocated = [math.floor(value) for value in exact]
    remainder = total - sum(allocated)
    order = sorted(
        range(len(weights)),
        key=lambda index: exact[index] - allocated[index],
        reverse=True,
    )
    for index in order[:remainder]:
        allocated[index] += 1
    return allocated

def compute_release_pnl(
    mfg: Manufacturing,
    fixed: ReleaseCosts,
    sales: SalesPlan,
    fees: ShopifyFees,
) -> Dict[str, float]:
    units_sold = int(round(mfg.units * sales.sell_through))
    gross_revenue = units_sold * sales.unit_price

    # Conservative: estimate orders from avg units/order
    est_orders = estimate_orders(units_sold, sales.avg_units_per_order)

    processing_fees = gross_revenue * fees.rate + est_orders * fees.fixed_per_order

    total_cost_basis = mfg.manufacturing_total + fixed.total
    net_profit_pre_tax = (gross_revenue - processing_fees) - total_cost_basis

    all_in_cost_per_unit = total_cost_basis / mfg.units
    # break-even price per unit including processing:
    # price * units - (price*units*rate + orders*fixed) = total_cost_basis
    # price * units * (1 - rate) = total_cost_basis + orders*fixed
    break_even_price = (total_cost_basis + est_orders * fees.fixed_per_order) / (units_sold * (1 - fees.rate)) if units_sold > 0 else float("inf")

    return {
        "units": mfg.units,
        "units_sold": units_sold,
        "manufacturing_total": mfg.manufacturing_total,
        "fixed_total": fixed.total,
        "total_cost_basis": total_cost_basis,
        "manufacturing_cost_per_unit": mfg.cost_per_unit,
        "all_in_cost_per_unit": all_in_cost_per_unit,
        "unit_price": sales.unit_price,
        "gross_revenue": gross_revenue,
        "est_orders": est_orders,
        "processing_fees": processing_fees,
        "net_profit_pre_tax": net_profit_pre_tax,
        "break_even_price_including_processing": break_even_price,
    }

def build_cashflow_timeline(
    mfg: Manufacturing,
    fixed: ReleaseCosts,
    sales: SalesPlan,
    fees: ShopifyFees,
    sched: CashFlowSchedule,
) -> List[Dict[str, object]]:
    """
    Returns a list of monthly rows:
      month_date, cash_in, cash_out, net, cumulative
    """
    # ---- Sales curve ----
    units_sold_total = int(round(mfg.units * sales.sell_through))
    months = sales.months_to_sell
    weights = sales.monthly_weights or default_sales_weights(months)
    if len(weights) != months:
        raise ValueError("monthly_weights must match months_to_sell length")

    units_by_month = allocate_integer_total(units_sold_total, weights)
    total_orders = estimate_orders(units_sold_total, sales.avg_units_per_order)
    orders_by_month = allocate_integer_total(total_orders, units_by_month)

    # ---- Timeline range ----
    # Start from earliest outflow month through last sales month
    start_month_offset = min(
        -sched.mfg_deposit_months_before_release,
        -sched.mfg_balance_months_before_release,
        -sched.mastering_months_before_release,
        -sched.artwork_months_before_release,
        min(sched.marketing_profile.keys()),
    )
    end_month_offset = max(0, months - 1)  # sales months start at offset 0

    rows: List[Dict[str, object]] = []
    cumulative = 0.0

    # Precompute cash events (by month offset)
    cash_out: Dict[int, float] = {}

    # manufacturing payments
    deposit = mfg.manufacturing_total * sched.mfg_deposit_pct
    balance = mfg.manufacturing_total - deposit

    cash_out[-sched.mfg_deposit_months_before_release] = cash_out.get(-sched.mfg_deposit_months_before_release, 0.0) + deposit
    cash_out[-sched.mfg_balance_months_before_release] = cash_out.get(-sched.mfg_balance_months_before_release, 0.0) + balance

    # fixed costs timing
    cash_out[-sched.mastering_months_before_release] = cash_out.get(-sched.mastering_months_before_release, 0.0) + fixed.mastering
    cash_out[-sched.artwork_months_before_release] = cash_out.get(-sched.artwork_months_before_release, 0.0) + fixed.artwork

    # marketing timing (profile)
    for mo, frac in sched.marketing_profile.items():
        cash_out[mo] = cash_out.get(mo, 0.0) + fixed.marketing * frac

    # Build monthly rows
    for mo in range(start_month_offset, end_month_offset + 1):
        d = add_months(sched.release_date, mo)

        # cash in from sales
        idx = mo  # sales start at 0
        cash_in = 0.0
        if 0 <= idx < months:
            u = units_by_month[idx]
            o = orders_by_month[idx]
            gross = u * sales.unit_price
            processing = gross * fees.rate + o * fees.fixed_per_order
            cash_in = gross - processing  # since customers pay shipping, we ignore outbound postage cost here

        out = cash_out.get(mo, 0.0)
        net = cash_in - out
        cumulative += net

        rows.append({
            "month": d.strftime("%Y-%m"),
            "cash_in_after_processing": cash_in,
            "cash_out": out,
            "net": net,
            "cumulative": cumulative,
            "detail": ""  # filled below
        })

    # Add simple labels to outflow months
    def add_detail(offset: int, label: str):
        r_index = offset - start_month_offset
        if 0 <= r_index < len(rows):
            rows[r_index]["detail"] = (rows[r_index]["detail"] + ("; " if rows[r_index]["detail"] else "") + label)

    add_detail(-sched.mfg_deposit_months_before_release, f"MFG deposit ({int(sched.mfg_deposit_pct*100)}%)")
    add_detail(-sched.mfg_balance_months_before_release, "MFG balance")
    add_detail(-sched.mastering_months_before_release, "Mastering")
    add_detail(-sched.artwork_months_before_release, "Artwork")
    for mo, frac in sched.marketing_profile.items():
        add_detail(mo, f"Marketing ({int(round(frac*100))}%)")

    # Find break-even month (first month cumulative >= 0)
    for r in rows:
        if r["cumulative"] >= 0:
            r["detail"] = (r["detail"] + ("; " if r["detail"] else "") + "Break-even reached")
            break

    return rows

# ---------- CLI Prompts ----------

def prompt_int(label: str, default: int) -> int:
    raw = input(f"{label} [{default}]: ").strip()
    return int(raw) if raw else default

def prompt_float(label: str, default: float) -> float:
    raw = input(f"{label} [{default}]: ").strip()
    return float(raw) if raw else default


def prompt_date(label: str, default: date) -> date:
    raw = input(f"{label} [{default.isoformat()}] (YYYY-MM-DD): ").strip()
    if not raw:
        return default
    year, month, day = raw.split("-")
    return date(int(year), int(month), int(day))


def print_pnl(result: Dict[str, float]) -> None:
    print("\n-------------------------------")
    print("MEOW RELEASE P&L (Summary)")
    print("-------------------------------")
    print(f"Units pressed:                {int(result['units'])}")
    print(f"Units sold (assumed):         {int(result['units_sold'])}")
    print(f"Manufacturing total:          {money(result['manufacturing_total'])}")
    print(f"Fixed release costs:          {money(result['fixed_total'])}")
    print(f"Total cost basis:             {money(result['total_cost_basis'])}")
    print(f"Manufacturing $/unit:         {money(result['manufacturing_cost_per_unit'])}")
    print(f"All-in $/pressed unit:        {money(result['all_in_cost_per_unit'])}")
    print("")
    print(f"Unit price:                   {money(result['unit_price'])}")
    print(f"Gross revenue:                {money(result['gross_revenue'])}")
    print(f"Estimated orders:             {int(result['est_orders'])}")
    print(f"Processing fees (estimated):  {money(result['processing_fees'])}")
    print(f"Net profit (pre-tax):         {money(result['net_profit_pre_tax'])}")
    print("")
    print(f"Break-even price (with fees): {money(result['break_even_price_including_processing'])}")


def print_cashflow(rows: List[Dict[str, object]]) -> None:
    print("\n----------------------------------------------")
    print("CASH-FLOW TIMELINE (Monthly, after processing)")
    print("----------------------------------------------")
    print(f"{'Month':<8}  {'Cash In':>12}  {'Cash Out':>12}  {'Net':>12}  {'Cumulative':>12}  Details")
    print("-" * 90)
    for row in rows:
        print(
            f"{row['month']:<8}  "
            f"{money(row['cash_in_after_processing']):>12}  "
            f"{money(row['cash_out']):>12}  "
            f"{money(row['net']):>12}  "
            f"{money(row['cumulative']):>12}  "
            f"{row['detail']}"
        )


def run_record_calculator() -> None:
    print("-----------------------------------")
    print(" MEOW RECORD RELEASE CALCULATOR v2 ")
    print("-----------------------------------\n")

    release_date = prompt_date("Release date", date.today())
    unit_price = prompt_float("Unit price ($)", 35.0)
    sell_through = prompt_float("Sell-through (0-1)", 1.0)
    months_to_sell = prompt_int("Months to sell through", 8)
    avg_units_per_order = prompt_float(
        "Average units per order (1.0 = conservative)",
        1.0,
    )
    units = prompt_int("Units pressed", 560)
    manufacturing_total = prompt_float(
        "Manufacturing total (landed invoice, $)",
        4294.05,
    )
    marketing = prompt_float("Marketing ($)", 5000.0)
    mastering = prompt_float("Mastering ($)", 2000.0)
    artwork = prompt_float("Artwork ($)", 1000.0)
    processing_rate_pct = prompt_float("Processing rate (%)", 2.9)
    processing_fixed = prompt_float("Fixed processing fee per order ($)", 0.30)

    manufacturing = Manufacturing(
        units=units,
        manufacturing_total=manufacturing_total,
    )
    release_costs = ReleaseCosts(
        marketing=marketing,
        mastering=mastering,
        artwork=artwork,
    )
    sales = SalesPlan(
        unit_price=unit_price,
        avg_units_per_order=avg_units_per_order,
        sell_through=sell_through,
        months_to_sell=months_to_sell,
    )
    fees = ShopifyFees(
        rate=processing_rate_pct / 100,
        fixed_per_order=processing_fixed,
    )
    schedule = CashFlowSchedule(
        release_date=release_date,
        mfg_deposit_pct=0.50,
        mfg_deposit_months_before_release=4,
        mfg_balance_months_before_release=2,
        mastering_months_before_release=3,
        artwork_months_before_release=3,
        marketing_profile={-1: 0.25, 0: 0.50, 1: 0.25},
    )

    result = compute_release_pnl(
        mfg=manufacturing,
        fixed=release_costs,
        sales=sales,
        fees=fees,
    )
    cashflow = build_cashflow_timeline(
        mfg=manufacturing,
        fixed=release_costs,
        sales=sales,
        fees=fees,
        sched=schedule,
    )

    print_pnl(result)
    print_cashflow(cashflow)
    print("\nAssumptions: customer-paid outbound postage and income taxes are excluded.")


def main() -> None:
    run_record_calculator()


if __name__ == "__main__":
    main()
