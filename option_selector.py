import pandas as pd
from datetime import date
import logging

_instruments_cache = None

def load_nfo_instruments(kite):
    global _instruments_cache
    if _instruments_cache is None:
        raw = kite.instruments("NFO")
        df  = pd.DataFrame(raw)
        _instruments_cache = df[df["name"] == "NIFTY"].copy()
    return _instruments_cache

def get_spot(kite):
    q = kite.quote("NSE:NIFTY 50")
    return q["NSE:NIFTY 50"]["last_price"]

def nearest_expiry(df):
    today    = date.today()
    expiries = sorted(df["expiry"].unique())
    upcoming = [e for e in expiries if e >= today]
    return upcoming[0] if upcoming else None

def pick_option(kite, signal):
    try:
        df     = load_nfo_instruments(kite)
        spot   = get_spot(kite)
        expiry = nearest_expiry(df)

        # round to nearest 50
        atm = round(spot / 50) * 50
        opt_type = "CE" if signal == "BUY_CE" else "PE"

        filtered = df[(df["expiry"] == expiry) & (df["strike"] == atm) & (df["instrument_type"] == opt_type)]

        if filtered.empty:
            logging.warning(f"No option found for {atm}{opt_type} expiry {expiry}")
            return None

        row = filtered.iloc[0]
        logging.info(f"Option selected: {row['tradingsymbol']}")
        return {
            "symbol":  row["tradingsymbol"],
            "token":   row["instrument_token"],
            "exchange": "NFO"
        }

    except Exception as e:
        logging.error(f"pick_option error: {e}")
        return None
