"""
====================================================================
PROJECT: Personal Finance & Portfolio Risk Engine (Interactive)
RUN    : Open in IDLE, Save, and press F5
NEEDS  : pip install numpy pandas yfinance   (only for the risk engine)
DATA   : Saved automatically to finance_data.json beside this script
====================================================================
"""

import copy
import json
import os
import re
import sys
from statistics import NormalDist

try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:  # e.g. pasted into a shell
    BASE_DIR = os.getcwd()

DATA_FILE = os.path.join(BASE_DIR, "finance_data.json")
WIDTH = 70
TRADING_DAYS = 252

# --------------------------------------------------------------------
# Data model
# Every collection is  {name: {field: value}}  so one generic editor
# can add / edit / remove entries in all of them.
# --------------------------------------------------------------------
COLLECTIONS = {
    "income": {
        "title": "Monthly Income Sources",
        "fields": [("amount", "Monthly amount", "money")],
        "primary": "amount",
    },
    "expenses": {
        "title": "Monthly Expenses",
        "fields": [("amount", "Monthly amount", "money")],
        "primary": "amount",
    },
    "savings": {
        "title": "Cash & Emergency Savings",
        "fields": [("amount", "Balance", "money")],
        "primary": "amount",
    },
    "debts": {
        "title": "Debts & Loans",
        "fields": [
            ("balance", "Outstanding balance", "money"),
            ("rate", "Interest rate (% per year)", "percent"),
            ("min_payment", "Minimum monthly payment", "money"),
        ],
        "primary": "balance",
    },
    "other_assets": {
        "title": "Other Assets (FD, PPF, property, funds...)",
        "fields": [("amount", "Current value", "money")],
        "primary": "amount",
    },
    "holdings": {
        "title": "Stock Holdings (ticker -> money invested)",
        "fields": [("amount", "Amount invested", "money")],
        "primary": "amount",
    },
}


def default_data():
    return {
        "settings": {
            "currency": "$",
            "risk_free_rate": 4.5,   # percent per year
            "period": "1y",          # yfinance period: 6mo, 1y, 2y, 5y ...
            "confidence": 95.0,      # VaR confidence level, percent
        },
        "income": {"Salary": {"amount": 5000.0}},
        "expenses": {"Living expenses": {"amount": 3200.0}},
        "savings": {"Emergency fund": {"amount": 12000.0}},
        "debts": {"Debt": {"balance": 4500.0, "rate": 0.0, "min_payment": 0.0}},
        "other_assets": {"Other investments": {"amount": 15000.0}},
        "holdings": {
            "AAPL": {"amount": 4000.0},
            "MSFT": {"amount": 3000.0},
            "GOOGL": {"amount": 3000.0},
        },
    }


def load_data():
    data = default_data()
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for key in data:
                if key in saved and isinstance(saved[key], dict):
                    if key == "settings":
                        data[key].update(saved[key])
                    else:
                        data[key] = saved[key]
        except (OSError, json.JSONDecodeError):
            print("[WARN] Could not read saved data file. Starting with defaults.")
    return data


def save_data():
    tmp = DATA_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, DATA_FILE)
    except OSError as e:
        print(f"[WARN] Could not save data: {e}")


data = load_data()


# --------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------
def divider(title=None):
    print("\n" + "=" * WIDTH)
    if title:
        print(f"  {title}")
        print("=" * WIDTH)


def pause():
    input("\nPress Enter to continue...")


def money(x):
    return f"{data['settings']['currency']}{x:,.2f}"


def fmt_field(value, kind):
    return f"{value:.2f}%" if kind == "percent" else money(value)


def ask_float(prompt, current=None, minimum=0.0):
    """Ask for a number. Enter keeps `current` (if given). Re-asks on bad input."""
    while True:
        hint = f" [{current:g}]" if current is not None else ""
        raw = input(f"  {prompt}{hint}: ").strip().replace(",", "")
        if raw == "":
            if current is not None:
                return current
            print("    A value is required.")
            continue
        try:
            value = float(raw)
        except ValueError:
            print("    Please enter a number.")
            continue
        if value != value or value in (float("inf"), float("-inf")):
            print("    Please enter a normal number.")
            continue
        if minimum is not None and value < minimum:
            print(f"    Value must be at least {minimum:g}.")
            continue
        return value


def total(key):
    field = COLLECTIONS[key]["primary"]
    return sum(rec.get(field, 0.0) for rec in data[key].values())


def pick_item(names, action):
    raw = input(f"  Number or name of item to {action} (blank = cancel): ").strip()
    if not raw:
        return None
    if raw.isdigit() and 1 <= int(raw) <= len(names):
        return names[int(raw) - 1]
    for n in names:
        if n.lower() == raw.lower():
            return n
    print("    No such item.")
    return None


# --------------------------------------------------------------------
# Generic add / edit / remove editor
# --------------------------------------------------------------------
def show_collection(key):
    spec = COLLECTIONS[key]
    items = data[key]
    if not items:
        print("  (nothing added yet)")
        return
    for i, (name, rec) in enumerate(items.items(), 1):
        parts = "  |  ".join(
            f"{label}: {fmt_field(rec.get(field, 0.0), kind)}"
            for field, label, kind in spec["fields"]
        )
        print(f"  {i:>2}. {name:<20} {parts}")
    print(f"\n  Total {spec['primary']}: {money(total(key))}")


def add_item(key):
    spec = COLLECTIONS[key]
    name = input("  Name (blank = cancel): ").strip()
    if not name:
        return
    if key == "holdings":
        name = name.upper()
        if not re.fullmatch(r"[A-Z0-9.\-^=]{1,15}", name):
            print("    That does not look like a valid ticker symbol.")
            return
    if name in data[key]:
        print(f"    '{name}' already exists. Use Edit instead.")
        return
    rec = {}
    for field, label, kind in spec["fields"]:
        rec[field] = ask_float(label)
    data[key][name] = rec
    save_data()
    print(f"  [OK] Added '{name}'.")


def edit_item(key):
    spec = COLLECTIONS[key]
    items = data[key]
    if not items:
        print("  Nothing to edit.")
        return
    name = pick_item(list(items), "edit")
    if name is None:
        return
    print("  Press Enter to keep the current value.")
    new_name = input(f"  Name [{name}]: ").strip()
    if key == "holdings":
        new_name = new_name.upper()
    rec = items[name]
    for field, label, kind in spec["fields"]:
        rec[field] = ask_float(label, current=rec.get(field, 0.0))
    if new_name and new_name != name:
        if new_name in items:
            print(f"    '{new_name}' already exists; keeping old name.")
        else:
            # rebuild dict so the entry keeps its position in the list
            data[key] = {(new_name if k == name else k): v for k, v in items.items()}
    save_data()
    print("  [OK] Updated.")


def remove_item(key):
    items = data[key]
    if not items:
        print("  Nothing to remove.")
        return
    name = pick_item(list(items), "remove")
    if name is None:
        return
    if input(f"  Really remove '{name}'? (y/n): ").strip().lower() == "y":
        del items[name]
        save_data()
        print(f"  [OK] Removed '{name}'.")
    else:
        print("  Cancelled.")


def manage_collection(key):
    while True:
        divider(COLLECTIONS[key]["title"].upper())
        show_collection(key)
        print("\n  [A] Add   [E] Edit   [R] Remove   [B] Back")
        choice = input("  Choice: ").strip().lower()
        if choice == "a":
            add_item(key)
        elif choice == "e":
            edit_item(key)
        elif choice == "r":
            remove_item(key)
        elif choice == "b":
            return
        else:
            print("  Please choose A, E, R or B.")


def manage_data_menu():
    menu = [
        ("1", "income"), ("2", "expenses"), ("3", "savings"),
        ("4", "debts"), ("5", "other_assets"), ("6", "holdings"),
    ]
    while True:
        divider("MANAGE YOUR DATA")
        for num, key in menu:
            print(f"  {num}. {COLLECTIONS[key]['title']}")
        print("  7. Back to main menu")
        choice = input("\n  Select (1-7): ").strip()
        if choice == "7":
            return
        for num, key in menu:
            if choice == num:
                manage_collection(key)
                break
        else:
            print("  Invalid choice.")


# --------------------------------------------------------------------
# 1. Personal financial health check
# --------------------------------------------------------------------
def health_check():
    divider("1. PERSONAL FINANCIAL HEALTH CHECK")

    income = total("income")
    expenses = total("expenses")
    cash = total("savings")
    invested = total("holdings")
    other = total("other_assets")
    debt = total("debts")
    min_pay = sum(d.get("min_payment", 0.0) for d in data["debts"].values())
    avg_rate = (
        sum(d.get("balance", 0.0) * d.get("rate", 0.0) for d in data["debts"].values()) / debt
        if debt > 0 else 0.0
    )

    monthly_savings = income - expenses
    savings_rate = monthly_savings / income * 100 if income > 0 else 0.0
    runway = cash / expenses if expenses > 0 else 0.0
    dti = min_pay / income * 100 if income > 0 else 0.0
    net_worth = cash + invested + other - debt

    print(f"  Monthly income      : {money(income)}")
    print(f"  Monthly expenses    : {money(expenses)}")
    print(f"  Monthly surplus     : {money(monthly_savings)}  (savings rate {savings_rate:.1f}%)")
    print(f"  Cash / emergency    : {money(cash)}  ({runway:.1f} months of expenses)")
    print(f"  Stock holdings      : {money(invested)}")
    print(f"  Other assets        : {money(other)}")
    print(f"  Total debt          : {money(debt)}  (avg rate {avg_rate:.1f}%)")
    print(f"  NET WORTH           : {money(net_worth)}")

    if data["expenses"] and income > 0:
        print("\n  Where your income goes:")
        for name, rec in sorted(data["expenses"].items(), key=lambda kv: -kv[1]["amount"]):
            print(f"    - {name:<20} {money(rec['amount']):>14}  ({rec['amount'] / income * 100:5.1f}% of income)")

    print("\n  Checklist:")
    if income <= 0:
        print("  [WARN] No income recorded, so ratios cannot be computed.")
    elif savings_rate >= 20:
        print("  [OK]     Savings rate is 20% or more.")
    elif savings_rate > 0:
        print("  [WARN]   Savings rate is under 20%. Try to save more of your income.")
    else:
        print("  [DANGER] Expenses exceed income (negative cash flow).")

    if expenses > 0:
        if runway >= 6:
            print("  [OK]     Emergency fund covers 6+ months.")
        elif runway >= 3:
            print("  [WARN]   Emergency fund covers 3-6 months. Consider building it up.")
        else:
            print("  [DANGER] Emergency fund covers less than 3 months.")

    if debt <= 0:
        print("  [OK]     No debt recorded.")
    else:
        if income > 0:
            if dti <= 36:
                print(f"  [OK]     Debt payments are {dti:.1f}% of income (36% or less).")
            else:
                print(f"  [WARN]   Debt payments are {dti:.1f}% of income (over 36%).")
        if avg_rate >= 8:
            print(f"  [WARN]   Average debt rate is {avg_rate:.1f}%. Paying it down may beat investing.")

    pause()


# --------------------------------------------------------------------
# 2. Portfolio risk engine
# --------------------------------------------------------------------
def risk_engine():
    divider("2. PORTFOLIO RISK ENGINE")

    try:
        import numpy as np
        import pandas as pd
        import yfinance as yf
    except ImportError:
        print("  Missing libraries. Install them with:")
        print("      pip install numpy pandas yfinance")
        pause()
        return

    holdings = data["holdings"]
    if not holdings:
        print("  No stock holdings yet. Add some under 'Manage data'.")
        pause()
        return

    s = data["settings"]
    tickers = list(holdings)
    print(f"  Assets : {', '.join(tickers)}")
    print(f"  Period : {s['period']}")
    print("  Downloading price history from Yahoo Finance...")

    try:
        raw = yf.download(tickers, period=s["period"], auto_adjust=True, progress=False)
        prices = raw["Close"]
    except Exception as e:
        print(f"\n  [ERROR] Could not fetch market data: {e}")
        pause()
        return

    if isinstance(prices, pd.Series):
        prices = prices.to_frame(tickers[0])

    # yfinance returns columns in alphabetical order, NOT in the order you typed
    # them, so always select by ticker name before applying weights.
    prices = prices.dropna(axis=1, how="all")
    missing = [t for t in tickers if t not in prices.columns]
    tickers = [t for t in tickers if t in prices.columns]
    if missing:
        print(f"  [WARN] No data for: {', '.join(missing)} (ignored). Check the symbols.")
    if not tickers:
        print("  [ERROR] No usable price history.")
        pause()
        return

    prices = prices[tickers].dropna()
    returns = prices.pct_change().dropna()
    if len(returns) < 30:
        print(f"  [ERROR] Only {len(returns)} days of overlapping data; need at least 30.")
        pause()
        return

    amounts = np.array([holdings[t]["amount"] for t in tickers], dtype=float)
    capital = amounts.sum()
    if capital <= 0:
        print("  [ERROR] Total invested amount must be greater than zero.")
        pause()
        return
    weights = amounts / capital

    # Portfolio statistics
    port = returns.dot(weights)
    mean_d, vol_d = port.mean(), port.std()
    ann_ret = mean_d * TRADING_DAYS
    ann_vol = vol_d * np.sqrt(TRADING_DAYS)
    rf = s["risk_free_rate"] / 100
    sharpe = (ann_ret - rf) / ann_vol if ann_vol > 0 else 0.0

    # Value at Risk
    conf = s["confidence"] / 100
    z = NormalDist().inv_cdf(conf)
    var_param = max(0.0, z * vol_d - mean_d)
    cutoff = np.percentile(port, (1 - conf) * 100)
    var_hist = max(0.0, -cutoff)
    cvar_hist = max(0.0, -port[port <= cutoff].mean())

    # Max drawdown
    growth = (1 + port).cumprod()
    max_dd = (growth / growth.cummax() - 1).min()

    print("\n" + "-" * WIDTH)
    print(" ALLOCATION")
    print("-" * WIDTH)
    for t, w, a in zip(tickers, weights, amounts):
        print(f"  {t:<8} {w * 100:>6.1f}%   {money(a):>16}")
    print(f"  {'TOTAL':<8} {100:>6.1f}%   {money(capital):>16}")

    print("\n" + "-" * WIDTH)
    print(" PER-ASSET (annualised)")
    print("-" * WIDTH)
    for t in tickers:
        r = returns[t].mean() * TRADING_DAYS
        v = returns[t].std() * np.sqrt(TRADING_DAYS)
        print(f"  {t:<8} return {r * 100:>7.2f}%   volatility {v * 100:>6.2f}%")

    if len(tickers) > 1:
        print("\n" + "-" * WIDTH)
        print(" CORRELATION MATRIX")
        print("-" * WIDTH)
        print(returns.corr().round(2).to_string())

    print("\n" + "-" * WIDTH)
    print(" PORTFOLIO RISK & RETURN")
    print("-" * WIDTH)
    print(f"  Expected annual return (historical) : {ann_ret * 100:>8.2f}%")
    print(f"  Annualised volatility               : {ann_vol * 100:>8.2f}%")
    print(f"  Sharpe ratio (Rf = {s['risk_free_rate']:g}%)          : {sharpe:>8.2f}")
    print(f"  Max drawdown over period            : {max_dd * 100:>8.2f}%")
    print(f"  1-day VaR {s['confidence']:g}% (parametric)      : {var_param * 100:>7.2f}%  = {money(capital * var_param)}")
    print(f"  1-day VaR {s['confidence']:g}% (historical)      : {var_hist * 100:>7.2f}%  = {money(capital * var_hist)}")
    print(f"  Expected shortfall (avg loss beyond VaR): {money(capital * cvar_hist)}")

    if ann_vol > 0.30:
        grade = "HIGH RISK"
    elif ann_vol > 0.18:
        grade = "MODERATE RISK"
    else:
        grade = "LOW RISK"
    print(f"  Risk classification                 : {grade}")

    print("\n" + "-" * WIDTH)
    print(" HOW TO READ THIS")
    print("-" * WIDTH)
    print(f"  On roughly {s['confidence']:g}% of normal trading days, you would expect to lose\n"
          f"  less than {money(capital * var_hist)} (historical method). On the other\n"
          f"  {100 - s['confidence']:g}% of days the loss can be larger, and VaR says nothing\n"
          f"  about how much larger. Past data does not guarantee future results.")
    pause()


# --------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------
def settings_menu():
    s = data["settings"]
    while True:
        divider("SETTINGS")
        print(f"  1. Currency symbol        : {s['currency']}")
        print(f"  2. Risk-free rate (%)     : {s['risk_free_rate']:g}")
        print(f"  3. History period         : {s['period']}   (e.g. 6mo, 1y, 2y, 5y)")
        print(f"  4. VaR confidence (%)     : {s['confidence']:g}")
        print("  5. Reset ALL data to defaults")
        print("  6. Back")
        choice = input("\n  Select (1-6): ").strip()

        if choice == "1":
            new = input("  New currency symbol: ").strip()
            if new:
                s["currency"] = new
        elif choice == "2":
            s["risk_free_rate"] = ask_float("Risk-free rate %", s["risk_free_rate"])
        elif choice == "3":
            new = input("  Period (6mo / 1y / 2y / 5y): ").strip().lower()
            if new in ("3mo", "6mo", "1y", "2y", "5y", "10y"):
                s["period"] = new
            else:
                print("    Not a supported period.")
        elif choice == "4":
            val = ask_float("Confidence %", s["confidence"], minimum=50.0)
            if val < 100:
                s["confidence"] = val
            else:
                print("    Must be below 100.")
        elif choice == "5":
            if input("  This erases everything you entered. Type YES to confirm: ").strip() == "YES":
                data.clear()
                data.update(copy.deepcopy(default_data()))
                s = data["settings"]
                print("  [OK] Reset to defaults.")
        elif choice == "6":
            save_data()
            return
        else:
            print("  Invalid choice.")
        save_data()


# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------
def main():
    while True:
        divider("PERSONAL FINANCE & PORTFOLIO RISK ENGINE")
        print("  1. Financial health check")
        print("  2. Portfolio risk engine (VaR, volatility, Sharpe, drawdown)")
        print("  3. Manage data (add / edit / remove)")
        print("  4. Settings")
        print("  5. Exit")
        choice = input("\n  Select (1-5): ").strip()

        if choice == "1":
            health_check()
        elif choice == "2":
            risk_engine()
        elif choice == "3":
            manage_data_menu()
        elif choice == "4":
            settings_menu()
        elif choice == "5":
            save_data()
            print("\n  Saved. Goodbye!\n")
            break
        else:
            print("  Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        save_data()
        print("\n\n  Interrupted. Data saved. Goodbye!")
        sys.exit(0)
