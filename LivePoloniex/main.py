#from tickerWebsocket import TradeSocket
from gapTickerWebsocket import TradeSocket
from signal import signal, SIGINT
from sys import exit

def handler(signal_received, frame):
    # Handle any cleanup here
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    exit(0)


if __name__ == "__main__":
    pair = "USDT_BTC"
    period_calc = 14400
    step_calc = 15
    do_on = True
    while do_on:
        try :
            socketCall = TradeSocket(pair, period_calc, step_calc)

            socketCall.ws.run_forever()
            if signal(SIGINT, handler):
                do_on = False
        except Exception as e:
            print(e)
