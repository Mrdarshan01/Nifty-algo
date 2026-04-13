import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import NIFTY_TOKEN
import logging

# using ema crossover + rsi. works well on nifty 5min charts
# tried MACD earlier but was getting too many false signals around 11am

def fetch_candles(kite, days=2):
    to_dt   = datetime.now()
    from_dt = to_dt - timedelta(days=days)
    data = kite.historical_data(
        instrument_token=NIFTY_TOKEN,
        from_date=from_dt,
        to_date=to_dt,
        interval="5minute"
    )
    df = pd.DataFrame(data)
    df.set_index("date", inplace=True)
    return df

def rsi(series, period=14):
    delta = series.diff()
    up   = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_up   = up.ewm(com=period-1, adjust=False).mean()
    avg_down = down.ewm(com=period-1, adjust=False).mean()
    rs = avg_up / avg_down
    return 100 - (100 / (1 + rs))

def get_signal(kite):
    try:
        df = fetch_candles(kite)
        df["ema9"]  = df["close"].ewm(span=9,  adjust=False).mean()
        df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()
        df["rsi14"] = rsi(df["close"])

        last = df.iloc[-1]
        prev = df.iloc[-2]

        cross_up   = prev["ema9"] < prev["ema21"] and last["ema9"] > last["ema21"]
        cross_down = prev["ema9"] > prev["ema21"] and last["ema9"] < last["ema21"]

        if cross_up and last["rsi14"] > 55:
            logging.info(f"BUY_CE signal | RSI={last['rsi14']:.1f} ema9={last['ema9']:.1f}")
            return "BUY_CE"
        elif cross_down and last["rsi14"] < 45:
            logging.info(f"BUY_PE signal | RSI={last['rsi14']:.1f} ema9={last['ema9']:.1f}")
            return "BUY_PE"
        else:
            return None

    except Exception as e:
        logging.error(f"signal error: {e}")
        return None
