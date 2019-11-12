#from tickerWebsocket import TradeSocket
from gapTickerWebsocket import TradeSocket

if __name__ == "__main__":
    pair = "USDT_BTC"
    period_calc = 14400
    step_calc = 15
    do_on = True
    while do_on:
        try :
            socketCall = TradeSocket(pair, period_calc, step_calc)

            socketCall.ws.run_forever()
        except KeyError:
            print("Clean Exit")
            do_on = False
        except Exception as e:
            print(e)
