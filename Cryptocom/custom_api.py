from Cryptocom.api import Api
import time


class CustomApi(Api):
	REF_AVAILABLE = "REF_AVAILABLE_ON_CRYPTO_COM"
	TO_BUY = "TO_BUY_ON_CRYPTO_COM"
	IN_ORDER = "IN_ORDER_ON_CRYPTO_COM"
	BOUGHT = "BOUGHT_ON_CRYPTO_COM"
	SOLD = "SOLD_ON_CRYPTO_COM"
	NAME = "CRYPTO_COM"
	SUCCESS = "SUCCESS"
	ERROR = "ERROR"
	_TIME = float(60)

	def setup(self, _status, _ref):
		self.set_command("public/get-instruments")
		self.call_public_api()
		_instruments = self.response['result']['instruments']
		for v in _instruments:
			_base_currency = v['base_currency']
			_quote_currency = v['quote_currency']
			_pair = v['instrument_name']
			_price_decimals = v['price_decimals']
			_quantity_decimals = v['quantity_decimals']
			if _base_currency in _status:
				if _quote_currency == _ref:
					if 'exchange' not in _status[_base_currency]:
						_status[_base_currency]['exchange'] = self.NAME
						_status[_base_currency]['pair'] = _pair
						_status[_base_currency]['price_decimals'] = _price_decimals
						_status[_base_currency]['quantity_decimals'] = _quantity_decimals
		return _status

	def log(self):
		_params = self.payload['params']
		print("PAYLOAD", self.payload)
		if self.response['code'] == 0:
			print("SUCCESS", _params)
		else:
			print("ERROR", self.response['code'], self.response['message'])
		pass

	def check_order(self, _tx_id, _amount, _pair):
		self.set_command("private/get-order-detail", order_id = _tx_id)
		self.call_private_api(11)
		self.log()
		_order_info = self.response['result']['order_info']
		_side = _order_info['side']
		_price = float(_order_info['price'])
		_quantity = float(_order_info['quantity'])
		_quantity_executed = float(_order_info['cumulative_quantity'])
		_status = _order_info['status']
		_rc = self.ERROR
		if _status == "FILLED":
			print("SUCCESS SIDE: %s CRYPTO_COM pair: %s price: %f quantity: %f" % (_side, _pair, _price, _quantity))
			_rc = self.SUCCESS
		elif _status in ["ACTIVE", "CANCELED"]:
			print("WARNING SIDE: %s CRYPTO_COM pair: %s price: %f quantity: %f %s" % (_side, _pair, _price, _quantity, _status))
			self.cancel_order(_pair, _tx_id)
			_amount = _quantity - _quantity_executed
			if _side == "BUY":
				self.set_command("public/get-ticker", instrument_name = _pair)
				self.call_public_api()
				_bid = self.response['result']['data']['b']
				_rc = self.optimized_buy(_pair, _bid, _amount)
			elif _side == "SELL":
				_rc = self.sell(_amount, _pair)
			else:
				print("ERROR CRYPTO_COM in check order _side %s not defined", _side)
		else:
			print("ERROR SIDE: %s CRYPTO_COM pair: %s price: %f quantity: %f status: %s " % (_side, _pair, _price, _quantity, _status))
		return _rc

	def get_decimals(self, _pair):
		self.set_command("public/get-instruments")
		self.call_public_api()
		self.call_public_api()
		_instruments = self.response['result']['instruments']
		for v in _instruments:
			_base_currency = v['base_currency']
			_quote_currency = v['quote_currency']
			if _pair == v['instrument_name']:
				return v['price_decimals'], v['quantity_decimals']

	def buy(self, _amount, _pair):
		self.set_command("public/get-ticker", instrument_name=_pair)
		self.call_public_api()
		_bid = self.response['result']['data']['b']
		_tx_id = self.optimized_buy(_pair, _bid, _amount / _bid)
		return _tx_id

	def optimized_buy(self, _pair, _bid, _quantity_input):
		_price_decimals, _quantity_decimals = self.get_decimals(_pair)
		_format = "{0:.%sf}" % _price_decimals
		_price = _format.format(float(_bid) - 1 / (10 ** _price_decimals))


		_value = float(_price)
		_format = "{0:.%sf}" % _quantity_decimals
		_quantity = _format.format(float(_quantity_input) - 1 / (10 ** _quantity_decimals))
		print("BUY CRYPTO_COM pair:%s price:%s quantity:%s" % (_pair, _price, _quantity))
		self.set_command("private/create-order", instrument_name=_pair, price=_price, quantity=_quantity, side="BUY", type="LIMIT")
		self.call_private_api(11)
		self.log()
		_tx_id = self.response['result']['order_id']
		return _tx_id

	def sell(self, _amount, _pair):
		_price_decimals, _quantity_decimals = self.get_decimals(_pair)

		self.set_command("public/get-ticker", instrument_name=_pair)
		self.call_public_api()
		_ask = self.response['result']['data']['k']

		_format = "{0:.%sf}" % _price_decimals
		_price = _format.format(_ask+1/(10**_price_decimals))

		_format = "{0:.%sf}" % _quantity_decimals
		_quantity = _format.format(_amount-1/(10**_quantity_decimals))

		print("SELL CRYPTO_COM amount:%s  pair:%s price:%s quantity:%s" % (_amount, _pair, _price, _quantity))
		self.set_command("private/create-order", instrument_name=_pair, price=_price, quantity = _quantity, side = "SELL", type = "LIMIT")
		self.call_private_api(12)
		self.log()
		_tx_id = self.response['result']['order_id']
		return _tx_id

	def cancel_order(self, _pair, _tx_id):
		print("CANCEL CRYPTO_COM pair: %s id: %s" % (_pair, _tx_id))
		self.set_command("private/cancel-order", instrument_name=_pair, order_id=_tx_id)
		self.call_private_api(11)
		self.log()

	def get_balance(self, _asset):
		self.set_command("private/get-account-summary", currency = _asset)
		self.call_private_api(11)
		_asset_balance = self.response['result']['accounts'][0]['available']
		return _asset, _asset_balance

	def withdraw(self, _asset, _address, _memo):
		_asset, _asset_balance = self.get_balance(_asset)
		print("WITHDRAWAL CRYPTO_COM currency:%s  amount:%f address:%s address_tag:%s" % (_asset, _asset_balance, _address, _memo))
		self.set_command("private/create-withdrawal", currency=_asset, amount=_asset_balance, address=_address, address_tag=_memo)
		self.call_private_api(-1)
		self.log()

	def get_ref_amount(self, _ref):
		print("GET REF AMOUNT CRYPTO.COM")
		_list_ref = ['USDT', 'DAI', 'USDC']
		_list_ref.pop(_list_ref.index(_ref))
		self.set_command("private/get-account-summary")
		self.call_private_api(11)
		self.log()
		for _asset in _list_ref:
			_asset, _amount = self.get_balance(_asset)
			if _amount > 0.1:
				_pair = _asset + "_" + _ref
				_check = self.sell(_amount, _pair)
				while _check != self.SUCCESS:
					time.sleep(self._TIME)
					assert _check != self.ERROR, "ERROR in get ref amount crypto com"
					_check = self.check_order(_check, _amount, _pair)

		_asset, _ref_amount = self.get_balance(_ref)
		print("REF AMOUNT CRYPTO_COM: %f %s" % (_ref_amount, _ref))
		return _ref_amount


