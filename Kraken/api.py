import requests
import hmac
import hashlib
import time
import json
import base64
import urllib

link_public = "https://api.kraken.com"
link_api = "https://api.kraken.com"
link_websocket = "ws.kraken.com"
list_public = ["/0/public/Time",
               "/0/public/SystemStatus",
               "/0/public/Assets",
               "/0/public/AssetPairs",
               "/0/public/Ticker",
               "/0/public/OHLC",
               "/0/public/Depth",
               "/0/public/Trades",
               "/0/public/Spread"
               ]
list_private = ["/0/private/Balance",
                "/0/private/TradeBalance",
                "/0/private/OpenOrders",
                "/0/private/ClosedOrders",
                "/0/private/QueryOrders",
                "/0/private/TradesHistory",
                "/0/private/QueryTrades",
                "/0/private/Ledgers",
                "/0/private/QueryLedgers",
                "/0/private/TradeVolume",
                "/0/private/AddExport",
                "/0/private/ExportStatus",
                "/0/private/RetrieveExport",
                "/0/private/AddOrder",
                "/0/private/CancelOrder",
                "/0/private/CancelAll",
                "/0/private/CancelAllOrdersAfter",
                "/0/private/DepositMethods",
                "/0/private/DepositAddresses",
                "/0/private/DepositStatus",
                "/0/private/WithdrawInfo",
                "/0/private/Withdraw",
                "/0/private/WithdrawStatus",
                "/0/private/WalletTransfer"
                ]

list_subscription = ["user.order.{instrument_name}",
                     "user.trade.{instrument_name}",
                     "user.balance",
                     "book.{instrument_name}.{depth}",
                     "ticker.{instrument_name}",
                     "trade.{instrument_name}",
                     "candlestick.{interval}.{instrument_name}"
                     ]


class Api:
    def __init__(self, path, exchange="kraken", link=link_public):
        """
        Parameters
        ----------
        link : String
            Warper for Crypto.com Api
            For information https://exchange-docs.crypto.com/spot/index.html
        """
        self.link = link
        self.headers = {}
        self.payload = {}
        with open(str(path)+"/Kraken/home/Env/.zshenv") as f:
            dict_info = json.load(f)
        self.api_key = dict_info[exchange]["key"]
        self.api_sign = dict_info[exchange]["sign"]
        self.response = ''

    def call_public_api(self):
        r = requests.get(self.link + self.payload['method'],
                         params=self.payload['params'])
        if r.status_code == 200:
            self.response = r.json()
            return self.response
        else:
            error_msg = "Error %s during get request" % r.status_code
            print(error_msg)

    def set_payload(self, data, url):
        postdata = urllib.parse.urlencode(data)
        # Unicode-objects must be encoded before hashing
        encoded = (str(data['nonce']) + postdata).encode()
        message = url.encode() + hashlib.sha256(encoded).digest()

        signature = hmac.new(base64.b64decode(self.api_sign), message, hashlib.sha512)
        self.headers['API-Key'] = self.api_key
        self.headers['API-Sign'] = base64.b64encode(signature.digest()).decode()

    def call_private_api(self):
        url = self.link + self.payload['method']
        data = self.payload['params']
        data['nonce'] = int(time.time() * 1000)
        self.set_payload(data, self.payload['method'])

        request = requests.post(url,
                                data=data,
                                headers=self.headers)
        self.response = request.json()
        return self.response

    def set_command(self, command, **kwargs):
        if (command in list_public) or (command in list_private):
            self.payload = {'method':  command, 'params': kwargs}
        else:
            error_msg = "Wrong link or command"
            print(error_msg)


if __name__ == "__main__":
    import pathlib

    _PATH = pathlib.Path(__file__).parent.absolute()

    KA = Api("C:/Users/Stéphane Barroso/Documents/GitHub/TradingIA")
    # KA.set_command("private/Balance", instrument_name="BTC_USDC",
    #                page_size=2)
    KA.set_command("/0/private/DepositMethods", asset="XLM")
    print(KA.call_private_api())
    method = KA.response['result'][0]['method']
    KA.set_command("/0/private/DepositAddresses", method = method, asset = "XLM")
    print(KA.call_private_api())
    KA.set_command("/0/private/Balance")
    print(KA.call_private_api())
    KA.set_command("/0/public/Ticker", pair="BTCUSDT")
    print(KA.call_public_api())
    # print(KA.response['result'])
    # print(KA.response['error'])
    # KA.set_command("public/AssetPairs")
    # KA.call_public_api()
    # print(KA.response['error'])
