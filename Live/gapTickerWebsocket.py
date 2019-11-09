import json
from threading import Thread
from livetrade import  get_amount
import websocket
from api import ConnectApi
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
        self.bid = {}
        self.ask = {}
        self.buy = 0
        self.p_time = 0
        self.rate_sell = 0
        self.rate_buy = float('Inf')
        self.asset1, self.asset2 = get_amount(self.pair)
        self.ws.on_open = self.on_open
        self.pa = ConnectApi("https://poloniex.com/tradingApi")
        self.on_trade = False
        self.current_order_buy = ''
        self.current_order_sell = ''

    def trade(self, bs, rate, amount):
        self.asset1, self.asset2 = get_amount(self.pair)
        self.pa.set_command("returnOpenOrders", "currencyPair", self.pair)
        response = self.pa.call_private_api()
        self.current_order_buy = []
        self.current_order_sell = []
        if bs == "buy":
            for i in response:
                if i["type"] == "buy":
                    self.current_order_buy = i["orderNumber"]
                    if self.current_order_buy:
                        self.pa.set_command("moveOrder",
                                            "orderNumber", self.current_order_buy,
                                            "rate", rate)
            if not response:
                self.pa.set_command(bs, "currencyPair", self.pair, "rate", rate,
                                    "amount", amount, "postOnly ", 1)
            response = self.pa.call_private_api()
        elif bs == "sell":
            for i in response:
                elif i["type"] == "sell":
                    self.current_order_sell = i["orderNumber"]
                    if self.current_order_sell:
                        self.pa.set_command("moveOrder",
                                            "orderNumber", self.current_order_sell,
                                            "rate", rate)
            if not response:
                self.pa.set_command(bs, "currencyPair", self.pair, "rate",
                                    rate, "amount", amount, "postOnly ", 1)
            response = self.pa.call_private_api()

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

            min_bid_plus = min_bid * 1.0001
            if self.rate_sell <= min_bid or self.rate_sell > min_bid_plus:
                self.rate_sell = min_bid_plus
                self.trade("sell", self.rate_sell, self.asset2)

            max_ask_plus = max_ask * 0.9999
            if self.rate_buy >= max_ask or self.rate_buy < max_ask_plus:
                self.rate_buy = max_ask_plus
                self.trade("buy", self.rate_buy, self.asset1/self.rate_buy)

    @staticmethod
    def on_error(self, error):
        print(error)
        self.on_close()

    def on_close(self):
        self.pa.set_command("cancelAllOrders", "currencyPair", self.pair)
        self.pa.call_private_api()
        print("### closed ###")
        print("Close time: %s" % time.ctime(time.time()))

    def on_open(self):
        print("ON OPEN")
 
        def run():
            self.ws.send(json.dumps({'command': 'subscribe',
                                     'channel': self.pair}))

        Thread(target=run).start()
