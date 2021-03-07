import requests
import hmac
import hashlib
import time
import json


link_public = "https://api.crypto.com/v2/"
link_api = "https://api.crypto.com/v2/"
link_websocket = "wss://stream.crypto.com/v2/market"
list_public = ["public/auth",
               "public/get-instruments",
               "public/get-book",
               "public/get-candlestick",
               "public/get-ticker",
               "public/get-trades",
               "public/respond-heartbeat"
               ]
list_private = ["private/set-cancel-on-disconnect",
                "private/get-cancel-on-disconnect",
                "private/create-withdrawal",
                "private/get-withdrawal-history",
                "private/get-deposit-history",
                "private/get-account-summary",
                "private/create-order",
                "private/cancel-order",
                "private/cancel-all-orders",
                "private/get-order-history",
                "private/cancelOrder",
                "private/get-open-orders",
                "private/get-order-detail",
                "private/get-trades"
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
    def __init__(self, path, exchange="cryptocom", link=link_public):
        """
        Parameters
        ----------
        link : String
            Warper for Crypto.com Api
            For information https://exchange-docs.crypto.com/spot/index.html
        """
        self.link = link
        self.headers = {'Content-Type': 'application/json'}
        self.payload = {}
        with open(str(path)+"/Cryptocom/home/Env/.zshenv") as f:
            dict_info = json.load(f)
        self.api_key = dict_info[exchange]["key"]
        self.api_sign = bytes(dict_info[exchange]["sign"], "utf8")
        self.response = ''

    def call_public_api(self):
        """
        Returns
        -------
        type : json
            Return response from the public api in json format
            see set_command to create your call
        """
        r = requests.get(self.link + self.payload['method'],
                         params=self.payload['params'])
        if r.status_code == 200:
            self.response = r.json()
            return self.response
        else:
            error_msg = "Error %s during get request" % r.status_code
            print(error_msg)

    def set_payload(self, _id):
        self.payload["api_key"] = self.api_key
        self.payload["id"] = _id
        self.payload["nonce"] = int(time.time() * 1000)
        req = self.payload
        params = req["params"]
        load = req['method'] + str(req['id']) + req['api_key']
        load = load + ''.join('{}{}'.format(*p) for p in sorted(params.items()))
        msg = bytes(load + str(req['nonce']), 'utf-8')

        self.payload['sig'] = hmac.new(self.api_sign, msg=msg,
                                       digestmod=hashlib.sha256).hexdigest()

    def call_private_api(self, _id):
        """
        Returns
        -------
        type : json
            Return response from the Trading api in json format
            see set_command to create your call
        """
        self.set_payload(_id)
        request = requests.post(self.link + self.payload['method'],
                                json=self.payload,
                                headers=self.headers)
        self.response = request.json()
        return self.response

    def set_command(self, command, **kwargs):
        """
        Parameters
        ----------
        command : String
            You can see all the command on https://poloniex.com/support/api/

        kwargs : multiple dict
            You can set the option like that:
            set_command("public/get-book", instrument_name="BTC_USDT",
                        page_size=2)
        """
        if (command in list_public) or (command in list_private):
            self.payload = {'method':  command, 'params': kwargs}
        else:
            error_msg = "Wrong link or command"
            print(error_msg)


if __name__ == "__main__":
    CA = Api()
    CA.set_command("private/get-open-orders", instrument_name="BTC_USDC",
                   page_size=2)
    print(CA.call_private_api(11))
    CA.set_command("public/get-book", instrument_name="BTC_USDT")
    CA.call_public_api()
    CA.set_command("public/get-instruments")
    CA.call_public_api()
