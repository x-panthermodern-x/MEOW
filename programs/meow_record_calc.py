
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Tuple, Optional
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

@dataclass
class ReleaseCosts:
    marketing: float = 5000.0
    mastering: float = 2000.0
    artwork: float = 1000.0

    @property
    def total(self) -> float:
        return self.marketing + self.mastering + self.artwork

@dataclass
class Manufacturing:
    units: int = 560
    manufacturing_total: float = 4294.05  # your AtoZ subtotal (includes inbound freight + delivery)

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
    marketing_profile: Dict[int, float] = None  # {month_offset: fraction_of_marketing}

    def __post_init__(self):
        if self.marketing_profile is None:
            self.marketing_profile = {-1: 0.25, 0: 0.50, 1: 0.25}
        # sanity check (soft)
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

def compute_release_pnl(
    mfg: Manufacturing,
    fixed: ReleaseCosts,
    sales: SalesPlan,
    fees: ShopifyFees,
) -> Dict[str, float]:
    units_sold = int(round(mfg.units * sales.sell_through))
    gross_revenue = units_sold * sales.unit_price

    # Conservative: estimate orders from avg units/order
    est_orders = math.ceil(units_sold / max(1e-9, sales.avg_units_per_order))

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
    months = max(0, int(sales.months_to_sell))
    weights = sales.monthly_weights or default_sales_weights(months)
    if len(weights) != months:
        raise ValueError("monthly_weights must match months_to_sell length")

    # Allocate unit sales by month (integers that sum exactly)
    units_by_month = [int(round(units_sold_total * w)) for w in weights]
    # fix rounding drift
    drift = units_sold_total - sum(units_by_month)
    i = 0
    while drift != 0 and months > 0:
        units_by_month[i % months] += 1 if drift > 0 else -1
        drift = units_sold_total - sum(units_by_month)
        i += 1

    # Estimate orders by month
    orders_by_month = [math.ceil(u / max(1e-9, sales.avg_units_per_order)) if u > 0 else 0 for u in units_by_month]

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
        processing = 0.0
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


def run_record_calculator():
    # Variables
    records = _prompt_int("Amount of Records", 2000)
    sell_price = _prompt_float("Price you are selling records at ($)", 35)
    unit_cost = _prompt_float("Record Unit Cost ($)", 6)
    mail_order_assistants = _prompt_int("Number of Mail Order Assistants", 4)
    mail_order_wage = _prompt_float("Mail Order Assistant $/hr", 20)
    packaging_cost = _prompt_float("Packaging Material Cost ($)", 3)
    records_per_day_min = _prompt_int("Records packed per day (min)", 100)
    records_per_day_max = _prompt_int("Records packed per day (max)", 160)
    records_per_day_range = (records_per_day_min, records_per_day_max)
    shipping_per_unit = _prompt_float("Shipping cost per unit ($)", 0.69)
    weight_per_record = _prompt_float("Weight per record (kg)", 0.2)

    var_dict = {
        'Amount of Records: ': records,
        'Price you are selling records at: $': sell_price,
        'Record Unit Cost: $': unit_cost,
        'Mail Order Assistant $/hr: $': mail_order_wage,
        "Packaging Material Cost: $": packaging_cost,
        "Number of Mail Order Assistants: ": mail_order_assistants,
    }

    # Calculate and print totals
    total_revenue, total_print_cost, total_records_per_day, days_needed, mail_order_total_wage, total_packaging_cost, shipping_cost, total_cost, income_tax, total_profit, records_per_assistant = record_calculator(
        records,
        sell_price,
        unit_cost,
        mail_order_wage,
        records_per_day_range,
        packaging_cost,
        mail_order_assistants,
        shipping_per_unit,
        weight_per_record,
    )

    for var_name, var_value in var_dict.items():
        print(f"{CYAN}{var_name}{var_value}{RESET}")

    print(f"\n{MAG}Records packed per day by each mail assistant:", records_per_assistant)
    print(
        f"{mail_order_assistants} Mail order Personnel can pack {total_records_per_day * days_needed} @ {total_records_per_day} records per day in {days_needed} days"
    )
    print(f"\n{CYAN}Calculated Totals:{RESET}")
    print(f"Total GROSS revenue: ${total_revenue}")

    print(f"{RED}Total Unit Print cost: ${total_print_cost}")
    print(f"Total cost to ship from pressing plant: ${shipping_cost}")
    print(f"Mail order assistant total wage: ${mail_order_total_wage}")
    print(f"Total packaging cost: ${total_packaging_cost}")
    print(f"Est Tax on NET profit: ${income_tax}")
    print(f"Total cost: ${total_cost}{RESET}")

    print(f"{GREEN}Total NET profit: ${total_profit}{RESET}")

    num_runs = 8
    total_costs = []
    total_profits = []

    for _ in range(num_runs):
        _, _, _, _, _, _, _, total_cost, _, total_profit, _ = record_calculator(
            records,
            sell_price,
            unit_cost,
            mail_order_wage,
            records_per_day_range,
            packaging_cost,
            mail_order_assistants,
            shipping_per_unit,
            weight_per_record,
        )
        total_costs.append(total_cost)
        total_profits.append(total_profit)

    # Calculate average Total Cost and Total Net Profit
    average_total_cost = sum(total_costs) / num_runs
    average_total_profit = sum(total_profits) / num_runs

    print(f"\n{CYAN}Average Total Cost after {num_runs} runs: ${average_total_cost:.2f}")
    print(f"Average Total Net Profit after {num_runs} runs: ${average_total_profit:.2f}{RESET}")


if __name__ == "__main__":
    main()
