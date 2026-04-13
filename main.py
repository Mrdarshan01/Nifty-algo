from kiteconnect import KiteConnect
import pandas as pd
import time, logging
from datetime import datetime, date
from config import API_KEY, API_SECRET, TOKEN_FILE
from token_manager import get_access_token
from signal_engine import get_signal
from option_selector import pick_option
from order_manager import enter_trade, manage_open_trades

logging.basicConfig(
    filename="logs/trade_log.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

def main():
    kite = KiteConnect(api_key=API_KEY)
    token = get_access_token(kite, API_SECRET, TOKEN_FILE)
    kite.set_access_token(token)

    logging.info("Bot started. Waiting for market open...")
    print("Bot is live. Watching Nifty...")

    open_trade = None

    while True:
        now = datetime.now().strftime("%H:%M")

        if now < "09:20":
            time.sleep(30)
            continue

        if now >= "15:15":
            print("Market closed. Exiting.")
            break

        # dont take new trades after 2:30
        if now < "14:30" and open_trade is None:
            signal = get_signal(kite)
            if signal in ("BUY_CE", "BUY_PE"):
                option = pick_option(kite, signal)
                if option:
                    open_trade = enter_trade(kite, option)

        if open_trade:
            open_trade = manage_open_trades(kite, open_trade)

        time.sleep(60)

if __name__ == "__main__":
    main()
