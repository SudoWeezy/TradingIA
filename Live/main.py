from tickerWebsocket import TradeSocket

if __name__ == "__main__":
    pair = "USDT_BTC"
    period_calc = 14400
    step_calc = 15

    socketCall = TradeSocket(pair, period_calc, step_calc)

    socketCall.ws.run_forever()
