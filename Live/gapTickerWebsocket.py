import json
from threading import Thread
from livetrade import get_trigger, get_amount
import websocket
from api import ConnectApi
import time
import pickle
from sys import stdout as st


class TradeSocket:
    def __init__(self, pair, period, step):
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp("wss://api2.poloniex.com/",
                                         on_message = self.on_message,
                                         on_error = self.on_error,
                                         on_close = self.on_close)
        self.pair = pair
        self.period = period
        self.step = step
        self.bid = {}
        self.ask = {}
        self.buy = 0
        self.p_time = 0
        self.asset1, self.asset2 = get_amount(self.pair)
        self.ws.on_open = self.on_open
        self.pa = ConnectApi("https://poloniex.com/tradingApi")
        self.on_trade = False

    def trade(self, bs, rate, amount):
        self.pa.set_command(bs, "currencyPair", self.pair, "rate", rate,
                            "amount", amount, "postOnly ", 1)
        print(self.pa.call_private_api())

    def on_message(self, message):
        json_msg = json.loads(message)
        if len(json_msg) > 2:
            for i in json_msg[2]:
                if i[0] == "o":
                    if i[1] == 1:
                        self.ask[i[2]] = i[3]
                        if float(i[3]) == 0:
                            self.ask.pop(i[2])
                    elif i[1] == 0:
                        self.bid[i[2]] = i[3]
                        if float(i[3]) == 0:
                            self.bid.pop(i[2])
                elif i[0] == "i":
                    self.bid = i[1]['orderBook'][0]
                    self.ask = i[1]['orderBook'][1]
                min_bid = min(map(float, self.bid.keys()))
                max_ask = max(map(float, self.ask.keys()))

            self.pa.set_command("cancelAllOrders", "currencyPair",
                                self.pair)
            print(self.pa.call_private_api())
            self.asset1, self.asset2 = get_amount(self.pair)
            rate = min_bid * 1.0005
            self.trade("sell", rate, self.asset2)
            rate = max_ask * 0.9995
            self.trade("buy", rate, self.asset1/rate)

    @staticmethod
    def on_error(self, error):
        print(error)

    @staticmethod
    def on_close(self):
        print("### closed ###")
        print("Close time: %s" % time.ctime(time.time()))
    

    def on_open(self):
        print("ON OPEN")
 
        def run():
            self.ws.send(json.dumps({'command': 'subscribe',
                                     'channel': self.pair}))
        Thread(target=run).start()
