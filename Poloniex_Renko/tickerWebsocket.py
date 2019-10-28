import json
from threading import Thread
from livetrade import live_trade_calculation
import websocket
from api import ConnectApi
# https://stackoverflow.com/questions/48398292/poloniex-websockets

from decimal import Decimal

def add_one(v):
    after_comma = Decimal(v).as_tuple()[-1]*-1
    add = Decimal(1) / Decimal(10**after_comma)
    return Decimal(v) + add

def minus_one(v):
    after_comma = Decimal(v).as_tuple()[-1]*-1
    add = Decimal(1) / Decimal(10**after_comma)
    return Decimal(v) - add

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
        self.asset1, self.asset2, self.sell, self.buy = 0, 0, 0, 0
        self.ws.on_open = self.on_open
        self.private_api = ConnectApi("https://poloniex.com/tradingApi")
        
    def make_trade(self, rate, bs):
        print("Should " + bs)
        if bs = "buy":
            print("BID:[" + "Rate: " + i[2] + " Amount: " + i[3] + "]")
            rate = minus_one(rate)
            self.trade(bs, rate, self.asset1/rate)
        elif bs = "sell":
            print("ASK:[" + "Rate: " + i[2] + " Amount: " + i[3] + "]")
            rate = add_one(rate)
            self.trade(bs, rate, self.asset(2))
        self.asset1, self.asset2, self.sell, self.buy = \
            live_trade_calculation(self.pair, self.period, self.step)
                
    def trade(self, bs, rate, amount):
        self.private_api("cancelAllOrders")
        self.private_api(bs, 
                         "currencyPair", self.pair, 
                         "rate", rate, 
                         "amount", self.asset1/rate
                         "postOnly", 1)
        
        
    def on_message(self, message):
        json_msg = json.loads(message)
        # if date time > preced datetime + period , self.asset1, self.asset2, self.sell, self.buy = \
        #             live_trade_calculation(self.pair, self.period, self.step)

        if len(json_msg) > 2:
            for i in json_msg[2]:
                if i[0] == "o":
                    if i[1] == 1 and float(i[2]) > self.buy and self.asset1 > 0:
                        self.make_trade(i[2], "buy")
                        
                    elif i[1] == 0 and float(i[2]) < self.sell and self.asset2 > 0:
                        self.make_trade(i[2], "sell")
                        

    def on_error(self, error):
        print(error)

    def on_close(self):
        print("### closed ###")

    def on_open(self):
        self.asset1, self.asset2, self.sell, self.buy = \
            live_trade_calculation(self.pair, self.period, self.step)
        print("ON OPEN")

        def run(*args):
            self.ws.send(json.dumps({'command': 'subscribe', 'channel':
                    self.pair}))

        Thread(target=run).start()


