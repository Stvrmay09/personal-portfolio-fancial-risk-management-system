# Personal Finance & Portfolio Risk Engine

A terminal app I built in Python to keep my personal finances and my stock portfolio in one place. It does two things: it tells you how healthy your money situation looks (savings rate, emergency fund, debt), and it measures how risky your stock portfolio is using real price data from Yahoo Finance.

Everything runs in the terminal, and your data stays on your own computer.

---

## What it does

**Financial health check**
- Monthly surplus and savings rate
- How many months of expenses your cash savings would cover
- Debt payments as a share of income, plus your average interest rate
- Net worth across cash, stocks, other assets and debts
- A simple checklist that flags what needs attention

**Portfolio risk engine**
- Annualised return and volatility
- Sharpe ratio (risk-free rate is adjustable)
- 1-day Value at Risk, calculated two ways: parametric and historical
- Expected shortfall (the average loss on the worst days)
- Maximum drawdown
- Per-stock stats and a correlation matrix

**Your data, your control**
- Add, edit and remove income, expenses, savings, debts, other assets and stock holdings
- Everything saves to `finance_data.json` automatically
- Change currency, risk-free rate, history period and VaR confidence in Settings

---

## Getting started

You need Python 3.8 or newer.

```bash
git clone https://github.com/Stvrmay09/<your-repo-name>.git
cd <your-repo-name>
pip install numpy pandas yfinance
python finance_engine.py
```

You can also open `finance_engine.py` in IDLE and press F5.

The health check works without any extra libraries. Only the risk engine needs `numpy`, `pandas` and `yfinance`, and it needs an internet connection to download prices.

---

## How to use it

The main menu has four options:

| Option | What it does |
|---|---|
| 1 | Shows your financial health check |
| 2 | Downloads prices and runs the risk analysis |
| 3 | Lets you add, edit or remove your data |
| 4 | Changes settings or resets everything |

The sample numbers that come with the app are placeholders. Replace them under **Manage data** first, otherwise the results describe someone else's finances.

For stock holdings you enter how much money you have in each ticker, not percentages. The app works out the weights itself.

---

## A few things worth knowing

- **VaR is an estimate.** It assumes the recent past is a fair guide to the near future. On the worst 5% of days (at 95% confidence) the loss can be much bigger than the VaR number.
- **Returns are historical.** The "expected annual return" is just the average of what happened over the period you chose. It is not a forecast.
- **Yahoo Finance data** is free but not guaranteed. If a ticker returns nothing, the app skips it and tells you.
- Non-US tickers need the Yahoo suffix, for example `RELIANCE.NS` for NSE stocks.

---

## Project layout

```
finance_engine.py    the whole app
finance_data.json    created on first run, holds your data (keep it private)
```

Add `finance_data.json` to your `.gitignore` if you fork this, so your personal numbers never end up on GitHub.

---

## Ideas for later

- Export a summary to PDF or CSV
- Charts for the portfolio (growth curve, drawdown)
- Monte Carlo simulation for VaR
- A debt payoff planner

---

## Disclaimer

This is a learning project, not financial advice. Please don't make investment decisions based only on its output.

---

## About me

I'm Mayank Singhal. I made this to practise Python and to get a better feel for how portfolio risk is measured.

- GitHub: [Stvrmay09](https://github.com/Stvrmay09)
- LinkedIn: [Mayank Singhal](https://www.linkedin.com/in/mayank-singhal-407783438/)

Feedback and suggestions are welcome, so feel free to open an issue.
