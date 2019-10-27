import json
from threading import Thread
from livetrade import live_trade_calculation
import websocket
from api import ConnectApi
# https://stackoverflow.com/questions/48398292/poloniex-websockets


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

    def on_message(self, message):
        json_msg = json.loads(message)
        # if date time > preced datetime + period , self.asset1, self.asset2, self.sell, self.buy = \
        #             live_trade_calculation(self.pair, self.period, self.step)

        if len(json_msg) > 2:
            for i in json_msg[2]:
                if i[0] == "o":
                    if i[1] == 1 and float(i[2]) > self.buy:
                        print("Should Buy")
                        print("BID:[" + "Value: " + i[2] + " Amount: " + i[3] + "]")
                    elif i[1] == 0 and float(i[2]) < self.sell:
                        print("Should Sell")
                        print("ASK:[" + "Value: " + i[2] + " Amount: " + i[3] + "]")

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


