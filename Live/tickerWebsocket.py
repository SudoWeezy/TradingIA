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
                            "amount", amount, "fillOrKill ", 1)
        trade_result = self.pa.call_private_api()
        if trade_result['resultingTrades']:
            self.on_trade = not self.on_trade            
            rate = float(trade_result['resultingTrades'][0]['rate'])
            print("Trade has been performed at rate: %f!" % rate)
            self.asset1, self.asset2 = get_amount(self.pair)
            self.init_atr()
            self.sell = rate - self.atr
            self.buy = rate + self.atr
            new_info = (self.atr, self.buy, self.sell)
            print("ATR: %f, BUY_Trig: %f, SELL_Trig: %f" % new_info)

    def on_message(self, message):
        json_msg = json.loads(message)
        if time.time() > (self.p_time + self.period):
            self.init_atr()
        if len(json_msg) <= 2:
            return
        for i in json_msg[2]:
            if i[0] != "o":
                continue
            if float(i[3]) <= 0:
                continue
            rate = float(i[2])
            if i[1] == 1 and rate > self.buy:
                self.buy += self.atr
                self.sell = self.buy - self.atr
                print("Update| SELL %f | BUY: %f" % (self.sell, self.buy))
                if not self.on_trade:
                    print("B:[Rate: " + i[2] + " Amount: " + i[3] + "]")
                    self.make_trade(rate, "buy")
            elif i[1] == 0 and rate < self.sell:
                self.sell -= self.atr
                self.buy = self.sell + self.atr
                print("Update| BUY: %f| SELL: f" % self.buy)
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
    
    def init_atr(self):
        p_time, self.atr = get_trigger(self.pair, self.period, self.step)
        if self.p_time != p_time:
            self.pa.set_command("returnTradeHistory", "currencyPair", self.pair)
            trade_history = self.pa.call_private_api()
            self.on_trade = trade_history[0]["type"] == "buy"
            self.sell = float(trade_history[0]["rate"]) - self.atr
            self.buy = float(trade_history[0]["rate"]) + self.atr
            self.p_time = p_time
            self.print_info()

    def print_info(self):
        print("Atr Datetime: %s" % time.ctime(self.p_time))
        print("Buy Trigger: %f Sell Trigger: %f" % (self.buy, self.sell))
        print("Current Datetime: %s" % time.ctime(time.time()))
        print("Pair %s : %f, %f" % (self.pair, self.asset1, self.asset2))
        print("On trade: %r" % self.on_trade)

    def on_open(self):
        print("ON OPEN")
        self.print_info()

        def run():
            self.ws.send(json.dumps({'command': 'subscribe',
                                     'channel': self.pair}))
        Thread(target=run).start()
