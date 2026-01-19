import random
import math

# ANSI escape codes
RED = "\033[31m"
GREEN = "\033[32m"
CYAN = "\033[36m"
MAG = "\033[35m"
RESET = "\033[0m"

# California tax brackets for 2021 (simplified)
tax_brackets = [
    (0, 9850, 0.01),
    (9851, 20250, 0.02),
    (20251, 40500, 0.04),
    (40501, 67500, 0.06),
    (67501, 405000, 0.08),
    (405001, 675000, 0.093),
    (675001, 1000000, 0.103),
    (1000001, 5000000, 0.113),
    (5000001, float('inf'), 0.123)
]

print("-----------------------------------")
print(f"{RED} MEOW RECORD PRODUCTION CALCULATOR{RESET}")
print("-----------------------------------\n")

def calculate_income_tax(net_profit, tax_brackets):
    tax = 0
    taxable_income = net_profit

    for low, high, rate in tax_brackets:
        if taxable_income > low:
            bracket_income = min(taxable_income, high) - low
            tax += bracket_income * rate
        else:
            break

    return tax

def record_calculator(records, sell_price, print_cost, mail_order_wage, records_per_day_range, packaging_cost, mail_order_assistants, shipping_per_unit, weight_per_record):
    # Calculate total revenue
    total_revenue = records * sell_price

    # Calculate total print cost
    total_print_cost = records * print_cost

    # Calculate number of records each mail assistant can pack per day
    records_per_assistant = [random.randint(records_per_day_range[0], records_per_day_range[1]) for _ in range(mail_order_assistants)]

    # Calculate number of days for mail order people to pack all records
    total_records_per_day = sum(records_per_assistant)
    days_needed = math.ceil(records / sum(records_per_assistant))

    # Calculate mail order people's total wage
    total_hours_needed = math.ceil(records / total_records_per_day) * 8
    mail_order_total_wage = total_hours_needed * mail_order_wage * mail_order_assistants

    # Calculate total packaging cost
    total_packaging_cost = records * packaging_cost

    # Calculate shipping costs
    shipping_cost = records * shipping_per_unit
    # Calculate income tax on net profit
    pre_tax_profit = total_revenue - (total_print_cost + total_packaging_cost + mail_order_total_wage + shipping_cost)
    income_tax = calculate_income_tax(pre_tax_profit, tax_brackets)

    # Calculate total cost
    total_cost = total_print_cost + total_packaging_cost + mail_order_total_wage + shipping_cost + income_tax

    # Calculate total profit
    total_profit = total_revenue - total_cost

    return total_revenue, total_print_cost, total_records_per_day, days_needed, mail_order_total_wage, total_packaging_cost, shipping_cost, total_cost, income_tax, total_profit, records_per_assistant

# Variables
records = 2000 #Total Amount of record your printing
sell_price = 35 #Price you are selling your records at
unit_cost = 6 #Average cost per vinyl unit
mail_order_assistants = 4 #How many people you are hiring to help you out
mail_order_wage = 20 #How much you are paying your assistants
records_per_day_range = (100, 160)  # Range for records packed per day by each mail assistant, we are accounting for the slackers here
packaging_cost = 3  # Assuming $3 per record for packaging cost to ship to fans
shipping_per_unit = 0.69 #based off atoz media this is $0.69
weight_per_record = 0.2 # Kilograms

var_dict = {'Amount of Records: ': records, 'Price you are selling records at: $': sell_price, 'Record Unit Cost: $': unit_cost, 'Mail Order Assistant $/hr: $': mail_order_wage, "Packaging Material Cost: $": packaging_cost, "Number of Mail Order Assistants: ": mail_order_assistants}

# Calculate and print totals
total_revenue, total_print_cost, total_records_per_day, days_needed, mail_order_total_wage, total_packaging_cost, shipping_cost, total_cost, income_tax, total_profit, records_per_assistant = record_calculator(records, sell_price, unit_cost, mail_order_wage, records_per_day_range, packaging_cost, mail_order_assistants, shipping_per_unit, weight_per_record)

for var_name, var_value in var_dict.items():
    print(f"{CYAN}{var_name}{var_value}{RESET}")

print(f"\n{MAG}Records packed per day by each mail assistant:", records_per_assistant)
print(f"{mail_order_assistants} Mail order Personnel can pack {total_records_per_day * days_needed} @ {total_records_per_day} records per day in {days_needed} days")
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
    _, _, _, _, _, _, _, total_cost, _, total_profit, _ = record_calculator(records, sell_price, unit_cost, mail_order_wage, records_per_day_range, packaging_cost, mail_order_assistants, shipping_per_unit, weight_per_record)
    total_costs.append(total_cost)
    total_profits.append(total_profit)

# Calculate average Total Cost and Total Net Profit
average_total_cost = sum(total_costs) / num_runs
average_total_profit = sum(total_profits) / num_runs

print(f"\n{CYAN}Average Total Cost after {num_runs} runs: ${average_total_cost:.2f}")
print(f"Average Total Net Profit after {num_runs} runs: ${average_total_profit:.2f}{RESET}")
