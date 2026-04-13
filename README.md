# Nifty-algo

# nifty-options-algo

Personal algo trading bot for Nifty weekly options. Built this in 2024 after getting tired of sitting in front of charts all day. Uses Zerodha Kite Connect API.

Not financial advice. Use at your own risk.

---

## What it does

- Watches Nifty 50 on 5-min candles
- Generates signal using EMA crossover (9/21) + RSI filter
- Buys ATM CE or PE on signal
- Places SL order immediately after entry
- Trails SL once 25% profit is hit
- Squares off at target or 3:10pm whichever comes first

---

## Setup

You need a Zerodha account with API access enabled (costs ₹2000/month).

```bash
pip install -r requirements.txt
```

Add your API key and secret to `config.py`.

First run will ask you to login via browser. After that the token gets saved locally for the day.

```bash
python main.py
```

---

## File structure

```
main.py            # entry point, main loop
config.py          # api keys, strategy params
token_manager.py   # handles kite login and daily token refresh
signal_engine.py   # ema crossover + rsi signal logic
option_selector.py # picks the right strike and expiry
order_manager.py   # entry, SL, trailing, exit
logs/              # trade logs go here
```

---

## Strategy

**Entry:**
- EMA9 crosses above EMA21 → BUY CE (if RSI > 55)
- EMA9 crosses below EMA21 → BUY PE (if RSI < 45)
- Only 1 trade at a time, intraday only (MIS)

**Exit:**
- SL: 30% of premium paid (placed as SL-M immediately after entry)
- Target: 50% profit on premium
- Trailing SL: kicks in at 25% profit, moves SL to entry+5%
- Hard exit at 3:10pm regardless

**No new trades after 2:30pm.**

---

## Notes

- Tested on Nifty weekly expiry. Works best on trending days, gets chopped on sideways markets.
- `NIFTY_TOKEN = 256265` is the instrument token for Nifty 50 index — this doesn't change.
- Lot size is 50. Set `MAX_LOTS` in config if you want to scale.
- Logs everything to `logs/trade_log.log`

---

## TODO

- [ ] Add VIX filter (avoid trading when VIX > 20)
- [ ] Backtest module
- [ ] Telegram alerts on entry/exit
- [ ] Auto login using selenium instead of manual paste
