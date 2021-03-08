from Cryptocom.api import Api as CApi
from Kraken.api import Api as KApi
import json
import sys
import pathlib
import time
_PATH = pathlib.Path(__file__).parent.absolute()

_KRAKEN = "KRAKEN"
_CRYPTO = "CRYPTO_COM"

_SUCCESS = "SUCCESS"
_ERROR = "ERROR"

_TO_TRANSFER = "TO_TRANSFER"

_WITHDREW = "WITHDREW"

_TIME_BETWEEN_ORDER = 300

_EXIT = 420


class CryptoApi(CApi):
	REF_AVAILABLE = "REF_AVAILABLE_ON_CRYPTO_COM"
	TO_BUY = "TO_BUY_ON_CRYPTO_COM"
	IN_ORDER = "IN_ORDER_ON_CRYPTO_COM"
	BOUGHT = "BOUGHT_ON_CRYPTO_COM"
	SOLD = "SOLD_ON_CRYPTO_COM"

	def setup(self, _status, _ref):
		self.set_command("public/get-instruments")
		_instruments = self.call_public_api()
		for v in _instruments['result']['instruments']:
			_base_currency = v['base_currency']
			_quote_currency = v['quote_currency']
			_pair = v['instrument_name']
			_price_decimals = v['price_decimals']
			_quantity_decimals = v['quantity_decimals']
			if _base_currency in _status:
				if _quote_currency == _ref:
					if 'exchange' not in _status[_base_currency]:
						_status[_base_currency]['exchange'] = _CRYPTO
						_status[_base_currency]['pair'] = _pair
						_status[_base_currency]['price_decimals'] = _price_decimals
						_status[_base_currency]['quantity_decimals'] = _quantity_decimals
		return _status

	def log(self):
		_params = self.payload['params']
		if self.response['code'] == 0:
			print("SUCCESS", _params)
		else:
			print("ERROR", self.response['message'], _params)
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
		_rc = _ERROR
		if _status == "FILLED":
			print("SUCCESS SIDE: %s CRYPTO_COM pair: %s price: %f quantity: %f" % (_side, _pair, _price, _quantity))
			_rc = _SUCCESS
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
		_instruments = self.call_public_api()
		for v in _instruments['result']['instruments']:
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
		# todo add check validate
		_price_decimals, _quantity_decimals = self.get_decimals(_pair)
		_format = "{0:.%sf}" % _price_decimals
		_price = _format.format(_bid - 1 / (10 ** _price_decimals))
		_value = float(_price)
		_format = "{0:.%sf}" % _quantity_decimals
		_quantity = _format.format(_quantity_input - 1 / (10 ** _quantity_decimals))
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


class KrakenApi(KApi):

	REF_AVAILABLE = "REF_AVAILABLE_ON_KRAKEN"
	TO_BUY = "TO_BUY_ON_KRAKEN"
	IN_ORDER = "IN_ORDER_ON_KRAKEN"
	BOUGHT = "BOUGHT_ON_KRAKEN"
	SOLD = "SOLD_ON_KRAKEN"

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
						_status[_base_currency]['exchange'] = _KRAKEN
						_status[_base_currency]['pair'] = _pair
						_status[_base_currency]['price_decimals'] = _price_decimals
						_status[_base_currency]['quantity_decimals'] = _quantity_decimals
		return _status

	def log(self):
		_params = self.payload['params']
		_method = self.payload['method']
		if not self.response['error']:
			print("SUCCESS", _method, _params)
		else:
			print("ERROR", self.response['error'], _method, _params)
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
		_rc = _ERROR
		if _status == "closed":
			print("SUCCESS SIDE: %s KRAKEN pair: %s price: %f quantity: %f" % (_side, _pair, _price, _quantity))
			_rc = _SUCCESS
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
		# todo add check validate
		_price_decimals, _quantity_decimals = self.get_decimals(_pair)
		_format = "{0:.%sf}" % _price_decimals
		_price = _format.format(_bid - 1 / (10 ** _price_decimals))
		_value = float(_price)
		_format = "{0:.%sf}" % _quantity_decimals
		_quantity = _format.format(_quantity_input - 1 / (10 ** _quantity_decimals))
		print("BUY KRAKEN pair:%s price:%s quantity:%s" % (_pair, _price, _quantity))
		self.set_command("/0/private/AddOrder", pair = _pair, price=_price, volume = _quantity, type = 'buy', ordertype = "limit")
		self.call_private_api()
		self.log()
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
		if self.response['error'][0] == 'EGeneral:Invalid arguments:volume':
			return _SUCCESS
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
		_asset_balance = float(self.response['result'][_asset_name])
		return _asset_name, _asset_balance

	def withdraw(self, _asset, _address, _memo):
		_asset, _asset_balance = self.get_balance(_asset)
		print("WITHDRAWAL KRAKEN currency:%f  amount:%s address:%s s" % (_asset, _asset_balance, _address))
		self.set_command("/0/private/Withdraw", asset = _asset, amount = _asset_balance, key = _address)
		self.call_private_api()
		self.log()


def run(**kwargs):
	_assert_error = "ERROR Missing reference ex: transfer=XLM"
	assert 'transfer' in kwargs, _assert_error
	_assert_error = "ERROR Missing reference ex: reference_crypto_com=USDT"
	assert 'reference_crypto_com' in kwargs, _assert_error
	_assert_error = "ERROR Missing reference ex: reference_kraken=XXBT"
	assert 'reference_kraken' in kwargs, _assert_error

	_transfer = kwargs['transfer']
	_ref_crypto_com = kwargs['reference_crypto_com']
	_ref_kraken = kwargs['reference_kraken']
	_crypto_api = CryptoApi(path=_PATH)
	_kraken_api = KrakenApi(path=_PATH)

	_config_file = str(_PATH)+"/config"
	assert (pathlib.Path(_config_file).exists())

	with open(_config_file) as f:
		_config = json.load(f)

	_status = _config["status"]
	_status = _kraken_api.setup(_status, _ref_kraken)
	_status = _crypto_api.setup(_status, _ref_crypto_com)

	_score_crypto = 0
	_score_kraken = 0
	for k, v in _status.items():
		if v['exchange'] == _KRAKEN:
			_status[k]['action'] = _kraken_api.TO_BUY
			_score_kraken = _score_kraken + v['score']
		elif v['exchange'] == _CRYPTO:
			_status[k]['action'] = _crypto_api.TO_BUY
			_score_crypto = _score_crypto + v['score']
		else:
			print("ASSET NOT AVAILABLE", k)

	_score_total = _score_crypto + _score_kraken
	_ref_amount_crypto_com = float(0)
	_ref_amount_kraken = float(0)

	_ref_amount_crypto_com = get_ref_amount_crypto_com(_crypto_api, _ref_crypto_com)
	assert _ref_amount_crypto_com > 1, "ERROR REF AMOUNT CRYPTO_COM to low"

	while _transfer in _status:
		time.sleep(_TIME_BETWEEN_ORDER)
		_status = transfer_from_crypto_to_kraken(_crypto_api, _transfer, _status, _ref_amount_crypto_com, _score_kraken, _score_total)
	dump_status(_status)
	_asset_name, _prev_amount = _kraken_api.get_balance(_transfer)
	_amount = _prev_amount
	while _prev_amount == _amount:
		_asset_name, _amount = _kraken_api.get_balance(_transfer)
		time.sleep(_TIME_BETWEEN_ORDER)

	_ref_amount_kraken = get_ref_amount_kraken(_kraken_api, _transfer, _status, _ref_kraken)
	assert _ref_amount_kraken > 0.001, "ERROR REF AMOUNT KRAKEN to low"
	while _status != {}:
		_status = action_on_crypto_com(_crypto_api, _transfer, _status, _ref_amount_crypto_com, _ref_crypto_com, _score_total)
		_status = action_on_kraken(_kraken_api, _transfer, _status, _ref_amount_kraken, _ref_kraken, _score_kraken)
		dump_status(_status)
		time.sleep(_TIME_BETWEEN_ORDER)


def dump_status(_status):
	_status_file = str(_PATH) + "/status"
	with open(_status_file, 'w') as f:
		json.dump(_status, f)
	exit(_EXIT)

def get_ref_amount_crypto_com(_crypto_api, _ref_crypto_com):
	_list_ref_crypto_com = ['CRO', 'USDT', 'DAI', 'USDC']
	_list_ref_crypto_com.pop(_list_ref_crypto_com.index(_ref_crypto_com))
	_crypto_api.set_command("private/get-account-summary")
	_accounts = _crypto_api.call_private_api(11)
	for _account in _accounts['result']['accounts']:
		_currency = _account['currency']
		if _currency in _list_ref_crypto_com:
			_amount = _account['available'] + _account['order']
			if _amount > 0.1:
				_pair = _currency+"_"+_ref_crypto_com
				_check = _crypto_api.sell(_amount, _pair)
				while _check != _SUCCESS:
					time.sleep(_TIME_BETWEEN_ORDER)
					assert _check != _ERROR, "ERROR in get ref amount crypto com"
					_check = _crypto_api.check_order(_check, _amount, _pair)

	_asset, _ref_amount_crypto_com = _crypto_api.get_balance(_ref_crypto_com)
	print("REF AMOUNT CRYPTO_COM: %f %s" % (_ref_amount_crypto_com, _ref_crypto_com))
	return _ref_amount_crypto_com


def transfer_from_crypto_to_kraken(_crypto_api, _transfer, _status, _ref_amount_crypto_com, _score_kraken, _score_total):
	v = _status[_transfer]
	k = _transfer
	_amount = _score_kraken / _score_total * _ref_amount_crypto_com
	_status = flow_status(_crypto_api, _status, v, k, _amount)
	return _status


def get_ref_amount_kraken(_kraken_api, _transfer, _status, _ref_kraken):
	_asset_name, _amount = _kraken_api.get_balance(_transfer)
	print('SUCCESS %s balance = %s' % (_transfer, _amount))
	_pair = _status[_asset_name]['pair']
	_check = _kraken_api.sell(_amount, _pair)
	while _check != _SUCCESS:
		time.sleep(_TIME_BETWEEN_ORDER)
		_check = _kraken_api.check_order(_check, _amount, _pair)
		assert _check != _ERROR, "ERROR in get ref amount kraken"
	_asset_name, _ref_amount_kraken = _kraken_api.get_balance(_ref_kraken)
	print("REF AMOUNT KRAKEN: %f %s" % (_ref_amount_kraken,  _ref_kraken))
	return _ref_amount_kraken


def action_on_crypto_com(_crypto_api, _transfer, _status, _ref_amount_crypto_com, _ref_crypto_com, _score_total):
	for k, v in _status.items():
		if v['exchange'] == _CRYPTO and v['score'] > 0:
			_score = v['score']
			_amount = _score / _score_total * _ref_amount_crypto_com
			_status = flow_status(_crypto_api, _status, v, k, _amount)
	return _status


def action_on_kraken(_kraken_api, _transfer, _status, _ref_amount_kraken, _ref_kraken, _score_kraken):
	for k, v in _status.items():
		if v['exchange'] == _KRAKEN and v['score'] > 0:
			_score = v['score']
			_amount = _score / _score_kraken * _ref_amount_kraken
			_status = flow_status(_kraken_api, _status, v, k, _amount)
	return _status


def flow_status(_api, _status, v, k, _amount):
	_action = v['action']
	_pair = v['pair']
	if _action == _api.TO_BUY:

		_tx_id = _api.buy(_amount, _pair)
		_status[k]['tx_id'] = _tx_id
		_status[k]['amount'] = _amount
		_status[k]['action'] = _api.IN_ORDER
	elif _action == _api.IN_ORDER:
		_tx_id = v['tx_id']
		_amount = v['amount']
		_check = _api.check_order(_tx_id, _amount, _pair)
		if _check == _SUCCESS:
			v['action'] = _api.BOUGHT
		elif _check != _ERROR:
			v['tx_id'] = _check
	elif _action == _api.BOUGHT:
		_asset_name, _amount = _api.get_balance(k)

		print("SUCCESS %f %s BOUGHT" % (_amount, k))
		_address = v['address']
		_memo = ""
		if "memo" in v:
			_memo = v['memo']
		_api.withdraw(k, _address, _memo)
		del _status[k]
	else:
		print("ERROR unexpected action %s" % v['action'])
	return _status


if __name__ == "__main__":
	_input = (arg.split('=') for arg in sys.argv[1:])
	try:
		run(**dict(_input))
	except AssertionError as e:
		print(e)