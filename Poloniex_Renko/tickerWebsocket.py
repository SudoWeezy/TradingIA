import json
from threading import Thread
from livetrade import live_trade_calculation
import websocket
from api import ConnectApi
from customfunc import add_one, minus_one
import time


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
        self.on_trade = False
        self.sell, self.buy = 0, 0
        self.asset1, self.asset2 = 0, 0
        self.p_time = 0
        self.ws.on_open = self.on_open
        self.private_api = ConnectApi("https://poloniex.com/tradingApi")
        
    def make_trade(self, rate, bs):
        print("Should " + bs)
        if bs == "buy":
            rate = rate * 1.01
            self.trade(bs, rate, self.asset1/rate)
        elif bs == "sell":
            rate = rate * 0.99
            self.trade(bs, rate, self.asset2)
        self.init_value()

    def trade(self, bs, rate, amount):
        self.private_api.set_command("cancelAllOrders", "currencyPair", self.pair)
        self.private_api.call_private_api()
        self.private_api.set_command(bs, "currencyPair", self.pair,
                                     "rate", rate,
                                     "amount", amount,
                                     "fillOrKill ", 1)
        #check if order is filled or not
            self.private_api.call_private_api()
            self.on_trade = not self.on_trade

    def on_message(self, message):
        json_msg = json.loads(message)
        if time.time() > (self.p_time + self.period):
            self.init_value()
        if len(json_msg) <= 2:
            return
        for i in json_msg[2]:
            if i[0] == "o":
                rate = float(i[2])
                print(i)
                if i[1] == 1 and rate > self.buy and not self.on_trade:
                    print("BID:[Rate: " + i[2] + " Amount: " + i[3] + "]")
                    self.make_trade(rate, "buy")

                elif i[1] == 0 and rate < self.sell and self.on_trade:
                    print("ASK:[Rate: " + i[2] + " Amount: " + i[3] + "]")
                    self.make_trade(rate, "sell")

    @staticmethod
    def on_error(self, error):
        print(error)

    @staticmethod
    def on_close(self):
        print("### closed ###")

    def init_value(self):
        self.on_trade, self.p_time, \
        self.sell, self.buy, \
        self.asset1, self.asset2 = \
            live_trade_calculation(self.pair, self.period, self.step)

    def on_open(self):
        self.init_value
        print("ON OPEN")

        def run(*args):
            self.ws.send(json.dumps({'command': 'subscribe',
                                     'channel': self.pair}))
        Thread(target=run).start()
