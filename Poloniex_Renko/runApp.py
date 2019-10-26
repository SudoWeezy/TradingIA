
import time
import datetime
import pandas as pd
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import matplotlib.pyplot as plt
import os.path
import numpy as np

import scipy.optimize as opt


def get_poloniex_data(s, e, pair, period):
    startTime = time.mktime(datetime.datetime.strptime(s, "%d_%m_%Y").timetuple())
    endTime = time.mktime(datetime.datetime.strptime(e, "%d_%m_%Y").timetuple())

    currentData = 'DataStorage//' + pair + '_' + s + '_' + e + "_" + str(period)


    parameters = {
        'command': 'returnChartData',
        'currencyPair': pair,
        'start': int(startTime),
        'end': int(endTime),
        'period': period
    }

    if os.path.isfile(currentData):
        df_data = pd.read_csv(currentData, sep='\t')
    else:
        try:
            session = Session()
            url = "https://poloniex.com/public?"
            response = session.get(url, params=parameters)
            df_data = pd.read_json(response.text)
            df_data.to_csv(currentData, sep='\t')
        except (ValueError, ConnectionError, Timeout, TooManyRedirects) as e:
            print(response.text)
            print(e)
    return df_data


def init_atr(high, low, close, step=14):
    atr = 0
    for i in range(1, step + 1):
        high_low = high._values[i] - low._values[i]
        high_close_prev = high._values[i] - close._values[i - 1]
        low_close_prev = low._values[i] - close._values[i - 1]
        tr = max(high_low, abs(high_close_prev), abs(low_close_prev))
        atr += tr
    atr = atr / step
    return atr


def calculation_atr1(high, low, close, step=14):
    atr = init_atr(high, low, close)
    start_value = close[step]
    list_atr = [start_value]

    for j in range(step, close.size - step):
        if close[j] > list_atr[-1] + atr:
            list_atr.append(list_atr[-1] + atr)
        elif close[j] < list_atr[-1] - atr:
            list_atr.append(list_atr[-1] - atr)
    print("score evaluation atr1: %f" % score_evaluation(list_atr, atr))
    return list_atr


def calculation_atr2(high, low, close, step=14):
    atr = init_atr(high, low, close)
    start_value = close[step]
    list_atr = [start_value]

    for j in range(step, close.size - step):
        idx_atr = j-step
        if close[j] > list_atr[-1] + atr:
            list_atr.append(list_atr[-1] + atr)
            if idx_atr + step < len(low):
                atr = init_atr(high[idx_atr:], low[idx_atr:], close[idx_atr:], step)
        elif close[j] < list_atr[-1] - atr:
            list_atr.append(list_atr[-1] - atr)
            if idx_atr + step < len(low):
                atr = init_atr(high[idx_atr:], low[idx_atr:], close[idx_atr:], step)
    return list_atr


def calculation_atr3(high, low, close, step=14):
    atr = init_atr(high, low, close)
    start_value = close[step]
    list_atr = [start_value]

    for j in range(step, close.size - step):
        idx_atr = j-step
        if close[j] > list_atr[-1] + atr:
            list_atr.append(list_atr[-1] + atr)

        elif close[j] < list_atr[-1] - atr:
            list_atr.append(list_atr[-1] - atr)

        if idx_atr + step < len(low) and j > step:
            atr = init_atr(high[idx_atr:], low[idx_atr:], close[idx_atr:], step)
    return list_atr


def score_evaluation(list_atr, price_ratio):
    balance = 0
    sign_changes = 0
    for i in range(1, len(list_atr)-1):
        if list_atr[i] > list_atr[i-1]:
            balance += 1
        elif list_atr[i] < list_atr[i-1]:
            balance += 1
        else:
            balance -= 2
        if list_atr[i] > list_atr[i-1] and list_atr[i] > list_atr[i+1]:
            sign_changes += 1
        elif list_atr[i] < list_atr[i-1] and list_atr[i] < list_atr[i+1]:
            sign_changes += 1
    if balance > 0:
        return np.log(balance/(max(sign_changes, 1)+1))*np.log(price_ratio)
    else:
        return -1


def buy_sell_simulation(list_atr):
    bank = [100]
    stock = [0]
    fees = 1-0.0050
    trade = False
    for i in range(1, len(list_atr)):
        if list_atr[i] > list_atr[i-1] and not trade:
            stock.append(bank[-1]/list_atr[i]*fees)
            bank.append(0)
            trade = True
        elif list_atr[i] < list_atr[i-1] and trade:
            bank.append(stock[-1]*list_atr[i]*fees)
            stock.append(0)
            trade = False
    return bank


if __name__ == "__main__":
    s = "01_01_2019"
    e = "26_10_2019"
    pair = 'USDT_BTC'
    period_list = [7200, 14400, 86400]
    step2_list = [10, 9, 4]
    step3_list = [8, 15, 7]
    i = 0
    for period in period_list:
        try:
            df_data = get_poloniex_data(s, e, pair, period)
            df_high = df_data['high']
            df_low = df_data['low']
            df_close = df_data['close']
            df_date = df_data['date']

            bank_final2 = 0
            bank_final3 = 0

            step2 = step2_list[i]
            step3 = step3_list[i]
            i += 1
            list_atr2 = calculation_atr2(df_high, df_low, df_close, step2)
            list_atr3 = calculation_atr3(df_high, df_low, df_close, step3)

            bank2 = buy_sell_simulation(list_atr2)
            bank3 = buy_sell_simulation(list_atr3)

            bank_final2 = bank2[-1] + bank2[-2]


            bank_final3 = bank3[-1] + bank3[-2]


            print("atr2 = %f, trades = %f, step2 = %f" %
                      (bank_final2, len(bank2), step2))
            print("atr3 = %f, trades = %f, step3 = %f" %
                  (bank_final3, len(bank3), step3))

            plt.figure(period)
            plt.subplot(511)
            plt.plot(df_close)
            plt.subplot(512)
            plt.plot(list_atr2)
            plt.subplot(513)
            plt.plot(bank2)
            plt.subplot(514)
            plt.plot(list_atr3)
            plt.subplot(515)
            plt.plot(bank3)

        except Exception as e:
            print(e)

    plt.show()
