
import time
import datetime
import pandas as pd
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import matplotlib.pyplot as plt
import os.path
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


def calculation_atr(high, low, close, step=14):
    atr = init_atr(high, low, close)
    start_value = close[step]
    list_atr = [start_value]

    for j in range(step, close.size - step):
        if close[j] > list_atr[-1] + atr:
            list_atr.append(list_atr[-1] + atr)
        elif close[j] < list_atr[-1] - atr:
            list_atr.append(list_atr[-1] - atr)
    return list_atr


def calculation_atr2(high, low, close, step=14):
    atr = init_atr(high, low, close)
    start_value = close[step]
    list_atr = [start_value]

    for j in range(step, close.size - step):
        index_atr = j-step
        if close[j] > list_atr[-1] + atr:
            list_atr.append(list_atr[-1] + atr)
            atr = init_atr(high[index_atr:], low[index_atr:], close[index_atr:])
        elif close[j] < list_atr[-1] - atr:
            list_atr.append(list_atr[-1] - atr)
            atr = init_atr(high[index_atr:], low[index_atr:], close[index_atr:])
    return list_atr





def buy_sell_simulation(list_atr):
    bank = [100]
    stock = [0]
    fees = 1-0.0025
    trade = False
    for i in range (1,len(list_atr)):
        if list_atr[i] > list_atr[i-1] and not trade:
            stock.append(bank[-1]/list_atr[i]*fees)
            bank.append(0)
            trade = True
        elif list_atr[i] < list_atr[i-1] and trade:
            bank.append(stock[-1]*list_atr[i]*fees)
            stock.append(0)
            trade = False

    return(bank)



if __name__ == "__main__":
    s = "01_05_2018"
    e = "26_10_2019"
    pair = 'USDT_BTC'
    period = '14400'
    try:
        df_data = get_poloniex_data(s, e, pair, period)
        df_high = df_data['high']
        df_low = df_data['low']
        df_close = df_data['close']
        df_date = df_data['date']

        list_atr1 = calculation_atr(df_high, df_low, df_close)
        list_atr2 = calculation_atr2(df_high, df_low, df_close)

        plt.figure(1)
        plt.subplot(511)
        plt.plot(df_close)
        plt.subplot(512)
        plt.plot(list_atr1)
        plt.subplot(514)
        plt.plot(list_atr2)
        plt.subplot(513)
        plt.plot(buy_sell_simulation(list_atr1))
        plt.subplot(515)
        plt.plot(buy_sell_simulation(list_atr2))
        plt.show()
    except Exception as e:
        print(e)