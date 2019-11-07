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
        self.atr = 0
        self.sell = 0
        self.buy = 0
        self.p_time = 0
        self.asset1, self.asset2 = get_amount(self.pair)
        self.ws.on_open = self.on_open
        self.pa = ConnectApi("https://poloniex.com/tradingApi")
        self.on_trade = False

    def make_trade(self, rate, bs):
        print("Should " + bs)
        if bs == "buy":
            rate = rate * 1.005
            self.trade(bs, rate, self.asset1/rate)
        elif bs == "sell":
            rate = rate * 0.995
            self.trade(bs, rate, self.asset2)

    def trade(self, bs, rate, amount):
        self.pa.set_command("cancelAllOrders", "currencyPair", self.pair)
        self.pa.call_private_api()
        self.pa.set_command(bs, "currencyPair", self.pair, "rate", rate,
                            "amount", amount, "postOnly ", 1)
        trade_result = self.pa.call_private_api()

    def on_message(self, message):
        json_msg = json.loads(message)
        if len(json_msg) <= 2:
            return
        for i in json_msg[2]:
            if i[0] != "o":
                continue
            if float(i[3]) <= 0:
                continue
            rate = float(i[2])
            if i[1] == 1 and rate > self.buy:
                if not self.on_trade:
                    print("B:[Rate: " + i[2] + " Amount: " + i[3] + "]")
                    self.make_trade(rate, "buy")
            elif i[1] == 0 and rate < self.sell:
                if self.on_trade:
                    print("A:[Rate: " + i[2] + " Amount: " + i[3] + "]")
                    self.make_trade(rate, "sell")

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
