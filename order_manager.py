from kiteconnect import KiteConnect
from config import LOT_SIZE, SL_PCT, TARGET_PCT
from datetime import datetime
import time, logging

def get_ltp(kite, symbol):
    q = kite.quote(f"NFO:{symbol}")
    return q[f"NFO:{symbol}"]["last_price"]

def enter_trade(kite, option):
    qty = LOT_SIZE  # 1 lot for now

    order_id = kite.place_order(
        variety=KiteConnect.VARIETY_REGULAR,
        exchange=KiteConnect.EXCHANGE_NFO,
        tradingsymbol=option["symbol"],
        transaction_type=KiteConnect.TRANSACTION_TYPE_BUY,
        quantity=qty,
        product=KiteConnect.PRODUCT_MIS,
        order_type=KiteConnect.ORDER_TYPE_MARKET
    )

    time.sleep(2)
    orders = kite.orders()
    entry_price = None
    for o in orders:
        if o["order_id"] == order_id:
            entry_price = o["average_price"]
            break

    if not entry_price:
        logging.warning("Couldnt get fill price, using LTP")
        entry_price = get_ltp(kite, option["symbol"])

    sl_price     = round(entry_price * (1 - SL_PCT), 1)
    target_price = round(entry_price * (1 + TARGET_PCT), 1)

    # place SL order right away
    sl_order_id = kite.place_order(
        variety=KiteConnect.VARIETY_REGULAR,
        exchange=KiteConnect.EXCHANGE_NFO,
        tradingsymbol=option["symbol"],
        transaction_type=KiteConnect.TRANSACTION_TYPE_SELL,
        quantity=qty,
        product=KiteConnect.PRODUCT_MIS,
        order_type=KiteConnect.ORDER_TYPE_SLM,
        trigger_price=sl_price
    )

    logging.info(f"ENTRY {option['symbol']} @ {entry_price} | SL={sl_price} target={target_price}")
    print(f"Entered {option['symbol']} @ ₹{entry_price} | SL ₹{sl_price} | Target ₹{target_price}")

    return {
        "symbol":       option["symbol"],
        "qty":          qty,
        "entry_price":  entry_price,
        "sl_price":     sl_price,
        "target_price": target_price,
        "sl_order_id":  sl_order_id,
        "trailed":      False
    }


def manage_open_trades(kite, trade):
    now = datetime.now().strftime("%H:%M")
    ltp = get_ltp(kite, trade["symbol"])

    pnl_pct = (ltp - trade["entry_price"]) / trade["entry_price"] * 100
    print(f"[{now}] {trade['symbol']} LTP={ltp} | P&L={pnl_pct:.1f}%")

    # target hit - exit
    if ltp >= trade["target_price"]:
        logging.info(f"TARGET HIT {trade['symbol']} @ {ltp}")
        _square_off(kite, trade)
        return None

    # move SL to breakeven once 25% profit
    if pnl_pct >= 25 and not trade["trailed"]:
        new_sl = round(trade["entry_price"] * 1.05, 1)  # 5% above entry as new SL
        try:
            kite.modify_order(
                variety=KiteConnect.VARIETY_REGULAR,
                order_id=trade["sl_order_id"],
                trigger_price=new_sl
            )
            trade["sl_price"]  = new_sl
            trade["trailed"]   = True
            logging.info(f"Trailing SL moved to {new_sl}")
            print(f"Trailing SL -> ₹{new_sl}")
        except Exception as e:
            logging.error(f"SL modify failed: {e}")

    # EOD exit
    if now >= "15:10":
        logging.info(f"EOD exit {trade['symbol']}")
        _square_off(kite, trade)
        return None

    return trade


def _square_off(kite, trade):
    # cancel existing SL first
    try:
        kite.cancel_order(variety=KiteConnect.VARIETY_REGULAR, order_id=trade["sl_order_id"])
    except:
        pass

    kite.place_order(
        variety=KiteConnect.VARIETY_REGULAR,
        exchange=KiteConnect.EXCHANGE_NFO,
        tradingsymbol=trade["symbol"],
        transaction_type=KiteConnect.TRANSACTION_TYPE_SELL,
        quantity=trade["qty"],
        product=KiteConnect.PRODUCT_MIS,
        order_type=KiteConnect.ORDER_TYPE_MARKET
    )
    print(f"Exited {trade['symbol']}")
