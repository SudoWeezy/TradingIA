from Cryptocom.api import Api as CryptoApi
from Kraken.api import Api as KrakenApi
import json
import sys
import pathlib
import time
_PATH = pathlib.Path(__file__).parent.absolute()

_KRAKEN = "KRAKEN"
_CRYPTO = "CRYPTO_COM"

_TO_BUY_ON_KRAKEN = "TO_BUY_ON_KRAKEN"
_IN_ORDER_ON_KRAKEN = "IN_ORDER_ON_KRAKEN"
_BOUGHT_ON_KRAKEN = "BOUGHT_ON_KRAKEN"
_SOLD_ON_KRAKEN = "SOLD_ON_KRAKEN"

_TO_BUY_ON_CRYPTO_COM = "TO_BUY_ON_CRYPTO_COM" 
_IN_ORDER_ON_CRYPTO_COM = "IN_ORDER_ON_CRYPTO_COM" 
_BOUGHT_ON_CRYPTO_COM = "BOUGHT_ON_CRYPTO_COM" 
_SOLD_ON_CRYPTO_COM = "SOLD_ON_CRYPTO_COM"

_WITHDREW = "WITHDREW"

def get_asset_info_crypto():
	pass
def get_pair_info_crypto_com():
	pass
def get_pair_info_kraken():
	pass





def withdraw_kraken(_api, _asset, _conf):
	pass
def withdraw_crypto_com(_api, _asset, _conf):
	pass
def get_account_summary_crypto_com():
	pass
def get_account_summary_kraken():
	pass


def buy_crypto_com(_api, _amount, _pair):
	_price_decimals, _quantity_decimals = get_decimals_crypto_com(_api, _pair)
	_format = "{0:.%sf}" % _quantity_decimals
	_quantity = _format.format(_amount-1/(10**_quantity_decimals))
	_api.set_command("private/create-order", instrument_name=_pair, notional=_quantity, side="BUY", type="MARKET")
	_api.call_private_api(11)
	crypto_log(_api)


def sell_crypto_com(_api, _amount, _pair):
	_price_decimals, _quantity_decimals = get_decimals_crypto_com(_api, _pair)
	_format = "{0:.%sf}" % _quantity_decimals
	_quantity = _format.format(_amount-1/(10**_quantity_decimals))
	_api.set_command("private/create-order", instrument_name = _pair, quantity = _quantity, side = "SELL", type = "MARKET")
	_api.call_private_api(12)
	crypto_log(_api)


def crypto_log(_api):
	_params = _api.payload['params']
	if _api.response['code'] == 0:
		print("SUCCESS", _params)
	else:
		print("ERROR", _api.response['message'], _params)
	pass


def get_decimals_crypto_com(_api, _pair):
	_api.set_command("public/get-instruments")
	_instruments = _api.call_public_api()
	for v in _instruments['result']['instruments']:
		_base_currency = v['base_currency']
		_quote_currency = v['quote_currency']
		if _pair == v['instrument_name']:
			return v['price_decimals'], v['quantity_decimals']


def setup_status_crypto_com(_api, _status, _ref):
	_api.set_command("public/get-instruments")
	_instruments = _api.call_public_api()
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


def setup_status_kraken(_api, _status, _ref):
	_api.set_command("/0/public/AssetPairs")
	_api.call_public_api()
	for k, v in _api.response['result'].items():
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


def kraken_log(_api):
	_api.call_private_api()
	_params = _api.payload['params']
	_method = _api.payload['method']
	if not _api.response['error']:
		print("SUCCESS", _method, _params)
	else:
		print("ERROR", _api.response['error'], _method, _params)
	pass


def buy_kraken(_api, _amount, _pair):
	_api.set_command("/0/public/AssetPairs", pair=_pair)
	_api.call_public_api()
	_quantity_decimals = _api.response['result'][_pair]['lot_decimals']
	_api.set_command("/0/public/Ticker", pair = _pair)
	_api.call_public_api()
	_price = float(_api.response['result'][_pair]['a'][0])
	_value = _amount / _price
	_format = "{0:.%sf}" % _quantity_decimals
	_quantity = _format.format(_value - 1 / (10 ** _quantity_decimals))
	_api.set_command("/0/private/AddOrder", ordertype = "market", pair = _pair, type = 'buy', volume = _quantity)
	_api.call_private_api()
	kraken_log(_api)
	pass


def sell_kraken(_api, _amount, _pair):
	_api.set_command("/0/public/AssetPairs", pair=_pair)
	_api.call_public_api()
	_quantity_decimals = _api.response['result'][_pair]['lot_decimals']
	_format = "{0:.%sf}" % _quantity_decimals
	_quantity = _format.format(_amount - 1 / (10 ** _quantity_decimals))
	_api.set_command("/0/private/AddOrder", ordertype = "market", pair = _pair, type = 'sell', volume = _quantity)
	_api.call_private_api()
	kraken_log(_api)
	pass


def get_kraken_asset_balance(_api, _asset):
	_api.set_command("/0/public/Assets", asset = _asset)
	_api.call_public_api()
	_asset_info = next(iter(_api.response['result'])),
	_asset_name = _asset_info[0]
	_api.set_command("/0/private/Balance")
	_api.call_private_api()
	kraken_log(_api)
	_asset_balance = float(_api.response['result'][_asset_name])
	return _asset_name, _asset_balance


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
	setup_status_kraken(_kraken_api, _status, _ref_kraken)
	setup_status_crypto_com(_crypto_api, _status, _ref_crypto_com)

	#set ref crypto.com
	_list_ref_crypto_com = ['CRO', 'USDT', 'DAI', 'USDC']
	_list_ref_crypto_com.pop(_list_ref_crypto_com.index(_ref_crypto_com))
	_crypto_api.set_command("private/get-account-summary")
	_accounts = _crypto_api.call_private_api(11)
	for _account in _accounts['result']['accounts']:
		_currency = _account['currency']
		if _currency in _list_ref_crypto_com:
			_amount = _account['available']
			if _amount > 0.001:
				_pair = _currency+"_"+_ref_crypto_com
				sell_crypto_com(_crypto_api, _amount, _pair)
	_crypto_api.set_command("private/get-account-summary", currency=_ref_crypto_com)
	_crypto_api.call_private_api(11)
	_ref_amount_crypto_com = _crypto_api.response['result']['accounts'][0]['available']

	_score_crypto = 0
	_score_kraken = 0
	for k, v in _status.items():
		if v['exchange'] == _KRAKEN:
			_status[k]['action'] = _TO_BUY_ON_KRAKEN
			_score_kraken = _score_kraken + _status[k]['score']
		elif v['exchange'] == _CRYPTO:
			_status[k]['action'] = _TO_BUY_ON_CRYPTO_COM
			_score_crypto = _score_crypto + _status[k]['score']
		else:
			print("ASSET NOT AVAILABLE", k)
	_score_total = _score_crypto + _score_kraken


	# buy transfer
	_amount = _score_kraken / _score_total * _ref_amount_crypto_com
	_pair = _status[_transfer]['pair']
	buy_crypto_com(_crypto_api, _amount, _pair)
	# transfer to kraken
	_crypto_api.set_command("private/get-account-summary", currency=_transfer)
	_crypto_api.call_private_api(11)
	_amount = _crypto_api.response['result']['accounts'][0]['available']
	_address = _status[_transfer]['kraken_address']
	_memo = _status[_transfer]['kraken_memo']
	_crypto_api.set_command("private/create-withdrawal", currency = _transfer, amount = _amount, address = _address, address_tag = _memo)
	_crypto_api.call_private_api(-1)
	crypto_log(_crypto_api)
	# buy crypto com
	for k, v in _status.items():
		if v['exchange'] == _CRYPTO and v['score'] > 0:
			_score = v['score']
			_amount = _score / _score_total * _ref_amount_crypto_com
			_pair = _status[_transfer]['pair']
			buy_crypto_com(_crypto_api, _amount, _pair)

			_crypto_api.set_command("private/get-account-summary", currency = k)
			_crypto_api.call_private_api(11)
			_amount = _crypto_api.response['result']['accounts'][0]['available']
			_address = _status[k]['ledger_address']

			_crypto_api.set_command("private/create-withdrawal", currency = k, amount = _amount, address = _address)
			_crypto_api.call_private_api(-1)
			crypto_log(_crypto_api)
	# set ref kraken
	_asset_name, _transfer_balance = get_kraken_asset_balance(_kraken_api, _transfer)
	print('SUCCESS %s balance = %s' % (_transfer, _transfer_balance))
	_pair = _status[_asset_name]['pair']
	sell_kraken(_kraken_api, _transfer_balance, _pair)
	_asset_name, _ref_amount_kraken = get_kraken_asset_balance(_kraken_api, _ref_kraken)
	for k, v in _status.items():
		if v['exchange'] == _KRAKEN and v['score'] > 0:
			_score = v['score']
			_amount = _score / _score_kraken * _ref_amount_kraken
			_pair = _status[k]['pair']
			buy_kraken(_kraken_api, _amount, _pair)
			_asset_name, _amount = get_kraken_asset_balance(_kraken_api, k)
			_key = _status[k]['key']
			_kraken_api.set_command("/0/private/Withdraw", asset = k, amount = _amount, key = _key)
			_kraken_api.call_private_api()
			kraken_log(_kraken_api)

	# withdraw
if __name__ == "__main__":
	try:
		_input = (arg.split('=') for arg in sys.argv[1:])
		run(**dict(_input))
	except AssertionError as e:
		print(e)
		exit(1)
