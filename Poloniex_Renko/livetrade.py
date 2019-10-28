from api import ConnectApi as ca
import datetime
from datetime import time
import pandas as pd
import time
import json

import requests


def atr_calculation(high, low, close, step=14):
    atr = 0
    for i in range(1, step + 1):
        high_low = high.values[i] - low.values[i]
        high_close_prev = high.values[i] - close.values[i - 1]
        low_close_prev = low.values[i] - close.values[i - 1]
        tr = max(high_low, abs(high_close_prev), abs(low_close_prev))
        atr += tr
    atr = atr / step
    return atr


def live_trade_calculation(pair, period_calc, step_calc):
    public_api = ca("https://poloniex.com/public")
    public_api.set_command("returnChartData",
                          "currencyPair", pair,
                          "period", period_calc,
                          "start", time.time() - period_calc * (step_calc + 3))

    df_data = pd.DataFrame(public_api.call_public_api())
    atr_calc = atr_calculation(df_data.high, df_data.low, df_data.close,
                               step_calc)

    private_api = ca("https://poloniex.com/tradingApi")
    private_api.set_command("returnBalances")
    current_balance = private_api.call_private_api()

    last_close = df_data.close.values[-1]

    asset1 = float(current_balance[pair.split("_")[0]])
    asset2 = float(current_balance[pair.split("_")[1]])
    sell_trigger = last_close - atr_calc
    buy_trigger = last_close + atr_calc
    time_calc = df_data.date.values[-1]

    on_trade = asset1 < (asset2 * last_close)
    return on_trade, time_calc, sell_trigger, buy_trigger, asset1, asset2

