from Kraken.api import Api

import time


class CustomApi(Api):
	REF_AVAILABLE = "REF_AVAILABLE_ON_KRAKEN"
	TO_BUY = "TO_BUY_ON_KRAKEN"
	IN_ORDER = "IN_ORDER_ON_KRAKEN"
	BOUGHT = "BOUGHT_ON_KRAKEN"
	SOLD = "SOLD_ON_KRAKEN"
	NAME = "KRAKEN"
	SUCCESS = "SUCCESS"
	ERROR = "ERROR"
	_TIME = 300

	def setup(self, _status, _ref):
		self.set_command("/0/public/AssetPairs")
		self.call_public_api()
		for k, v in self.response['result'].items():
			_base_currency = v['base']
			_quote_currency = v['quote']
			_pair = k
			_price_decimals = v['pair_decimals']
			_quantity_decimals = v['lot_decimals']
			if _base_currency in _status:
				if _quote_currency == _ref:
					if 'exchange' not in _status[_base_currency]:
						_status[_base_currency]['exchange'] = self.NAME
						_status[_base_currency]['pair'] = _pair
						_status[_base_currency]['price_decimals'] = _price_decimals
						_status[_base_currency]['quantity_decimals'] = _quantity_decimals
		return _status

	def log(self):
		print("PAYLOAD", self.payload)
		if not self.response['error']:
			print("SUCCESS", self.response['result'])
		else:
			print("ERROR", self.response['error'])
		pass

	def check_order(self, _tx_id, _amount, _pair):
		self.set_command("/0/private/QueryOrders", txid=_tx_id, trades="true")
		self.call_private_api()
		self.log()
		_order_info = self.response['result'][_tx_id]
		_side = _order_info['descr']['type']
		_price = float(_order_info['descr']['price'])
		_quantity = float(_order_info['vol'])
		_quantity_executed = float(_order_info['vol_exec'])
		_status = _order_info['status']
		_rc = self.ERROR
		if _status == "closed":
			print("SUCCESS SIDE: %s KRAKEN pair: %s price: %f quantity: %f" % (_side, _pair, _price, _quantity))
			_rc = self.SUCCESS
		elif _status in ["open", "canceled"]:
			print("WARNING SIDE: %s KRAKEN pair: %s price: %f quantity: %f %s" % (_side, _pair, _price, _quantity, _status))
			self.cancel_order(_pair, _tx_id)
			_amount = _quantity - _quantity_executed
			if _side == "buy":
				self.set_command("/0/public/Ticker", pair = _pair)
				self.call_public_api()
				_bid = self.response['result'][_pair]['b'][0]
				_rc = self.optimized_buy(_pair, _bid, _amount)
			elif _side == "sell":
				_rc = self.sell(_amount, _pair)
			else:
				print("ERROR KRAKEN in check order _side %s not defined", _side)
		else:
			print("ERROR SIDE: %s KRAKEN pair: %s price: %f quantity: %f status: %s " % (_side, _pair, _price, _quantity, _status))
		return _rc

	def get_decimals(self, _pair):
		self.set_command("/0/public/AssetPairs", pair=_pair)
		self.call_public_api()
		_quantity_decimals = self.response['result'][_pair]['lot_decimals']
		_price_decimals = self.response['result'][_pair]['pair_decimals']
		return _price_decimals, _quantity_decimals

	def buy(self, _amount, _pair):
		self.set_command("/0/public/Ticker", pair = _pair)
		self.call_public_api()
		_bid = float(self.response['result'][_pair]['b'][0])
		_tx_id = self.optimized_buy(_pair, _bid, _amount / _bid)
		return _tx_id

	def optimized_buy(self, _pair, _bid, _quantity_input):
		_price_decimals, _quantity_decimals = self.get_decimals(_pair)
		_format = "{0:.%sf}" % _price_decimals
		_price = _format.format(float(_bid) - 1 / (10 ** _price_decimals))
		_value = float(_price)
		_format = "{0:.%sf}" % _quantity_decimals
		_quantity = _format.format(float(_quantity_input) - 1 / (10 ** _quantity_decimals))
		print("BUY KRAKEN pair:%s price:%s quantity:%s" % (_pair, _price, _quantity))
		self.set_command("/0/private/AddOrder", pair = _pair, price=_price, volume = _quantity, type = 'buy', ordertype = "limit")
		self.call_private_api()
		self.log()
		if self.response['error'] and self.response['error'][0] == 'EGeneral:Invalid arguments:volume':
			return self.SUCCESS	
		elif self.response['error'] and self.response['error'][0] == 'EOrder:Insufficient funds':
			_tx_id = optimized_buy(self, _pair, _bid, _quantity_input*0.99)
		else:
			_tx_id = self.response['result']['txid'][0]
		return _tx_id

	def sell(self, _amount, _pair):
		_price_decimals, _quantity_decimals = self.get_decimals(_pair)
		self.set_command("/0/public/Ticker", pair = _pair)
		self.call_public_api()
		_ask = float(self.response['result'][_pair]['a'][0])

		_format = "{0:.%sf}" % _price_decimals
		_price = _format.format(_ask+1/(10**_price_decimals))

		_format = "{0:.%sf}" % _quantity_decimals
		_quantity = _format.format(_amount-1/(10**_quantity_decimals))

		print("SELL KRAKEN amount:%f  pair:%s price:%s quantity:%s" % (_amount, _pair, _price, _quantity))
		self.set_command("/0/private/AddOrder", pair=_pair, price=_price, volume=_quantity, type = 'sell', ordertype = "limit")
		self.call_private_api()
		self.log()
		if self.response['error'] and self.response['error'][0] == 'EGeneral:Invalid arguments:volume':
			return self.SUCCESS
		_tx_id = self.response['result']['txid'][0]
		return _tx_id

	def cancel_order(self, _pair, _tx_id):
		print("CANCEL KRAKEN pair: %s id: %s" % (_pair, _tx_id))
		self.set_command("/0/private/CancelOrder", txid=_tx_id)
		self.call_private_api()
		self.log()

	def get_balance(self, _asset):
		self.set_command("/0/public/Assets", asset = _asset)
		self.call_public_api()
		_asset_info = next(iter(self.response['result'])),
		_asset_name = _asset_info[0]
		self.set_command("/0/private/Balance")
		self.call_private_api()
		self.log()
		_asset_balance = 0
		if _asset_name in self.response['result']:
			_asset_balance = float(self.response['result'][_asset_name])
		return _asset_name, _asset_balance

	def withdraw(self, _asset, _address, _memo):
		_asset, _asset_balance = self.get_balance(_asset)
		print("WITHDRAWAL KRAKEN currency:%s  amount:%s address:%s" % (_asset, _asset_balance, _address))
		self.set_command("/0/private/Withdraw", asset = _asset, amount = _asset_balance, key = _address)
		self.call_private_api()
		self.log()

	def get_ref_amount(self, _transfer, _status, _ref):
		print("GET REF AMOUNT KRAKEN")
		_asset_name, _amount = self.get_balance(_transfer)
		_pair = _status[_asset_name]['pair']
		_check = self.sell(_amount, _pair)
		while _check != self.SUCCESS:
			time.sleep(self._TIME)
			_check = self.check_order(_check, _amount, _pair)
			assert _check != self.ERROR, "ERROR in get ref amount kraken"
		_asset_name, _ref_amount = self.get_balance(_ref)
		print("REF AMOUNT KRAKEN: %f %s" % (_ref_amount, _ref))
		return _ref_amount
