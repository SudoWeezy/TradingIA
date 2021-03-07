from Cryptocom.api import Api as CryptoApi
from Kraken.api import Api as KrakenApi
import json
import sys
import pathlib
import time
_PATH = pathlib.Path(__file__).parent.absolute()

_TO_BUY_ON_KRAKEN = "TO_BUY_ON_KRAKEN"
_IN_ORDER_ON_KRAKEN = "IN_ORDER_ON_KRAKEN"
_BOUGHT_ON_KRAKEN = "BOUGHT_ON_KRAKEN"
_SOLD_ON_KRAKEN = "_SOLD_ON_KRAKEN"

_TO_BUY_ON_CRYPTO_COM = "TO_BUY_ON_CRYPTO_COM" 
_IN_ORDER_ON_CRYPTO_COM = "IN_ORDER_ON_CRYPTO_COM" 
_BOUGHT_ON_CRYPTO_COM = "BOUGHT_ON_CRYPTO_COM" 
_SOLD_ON_CRYPTO_COM = "_SOLD_ON_CRYPTO_COM"

_WITHDREW = "WITHDREW"


def buy_crypto_com(k, v, _crypto_api, _sum_score, _ref_amount, _reference_crypto_com):
	_pair = v['pair']
	_price_decimals = v['price_decimals']
	_quantity_decimals = v['quantity_decimals']

	_crypto_api.set_command("public/get-ticker", instrument_name=_pair)
	_tickers = _crypto_api.call_public_api()

	_data = _tickers['result']['data']
	len(str(_data['a']).split('.')[1])
	_price = truncate_min(_data['a'], _price_decimals)
	_score = float(v['score']) / _sum_score
	_value = truncate_min(_score * _ref_amount / _price, _quantity_decimals)
	_amount = _value * _price
	_crypto_api.set_command("private/cancel-all-orders", instrument_name=_pair)
	_crypto_api.call_private_api(11)
	call_with_log(_crypto_api)

	print("Buy %f %s at %f for %f %s" % (_value, k, _price, _amount, _reference_crypto_com))
	_crypto_api.set_command("private/create-order",
					instrument_name=_pair,
					price=_price,
					quantity=_value,
					side="BUY",
					type="LIMIT")
	_crypto_api.call_private_api(11)
	call_with_log(_crypto_api)


def buy_kraken(k, v, _kraken_api, _sum_score, _ref_amount, _reference_kraken):
	_pair = v['pair']
	_price_decimals = v['price_decimals']
	_quantity_decimals = v['quantity_decimals']

	_kraken_api.set_command("/0/public/Ticker", pair = _pair)
	_kraken_api.call_public_api()
	_price = _kraken_api.response['result'][_pair]['a'][0]
	_price_trunc = truncate_min(float(_price), _price_decimals)
	_score = float(v['score']) / _sum_score
	_value = truncate_min(_score * _ref_amount / _price_trunc, _quantity_decimals)
	_format = "{0:.%sf}" % _price_decimals
	_price_format = _format.format(_price_trunc)
	_format = "{0:.%sf}" % _quantity_decimals
	_value_format = _format.format(_value)

	_kraken_api.set_command("/0/private/AddOrder", ordertype = "limit", pair = _pair, type = 'buy', volume = _value_format, price = _price_format)
	_kraken_api.call_private_api()
	kraken_call_with_log(_kraken_api)
	# catch error
	if _kraken_api.response['error']:
		print("WARNING cannot buy %s" % k, _kraken_api.response['error'][0])
	else:
		_txid = _kraken_api.response['result']['txid'][0]
		v['order_id'] = _txid
		v['status'] = _IN_ORDER_ON_KRAKEN
	return v


def call_with_log(_api):
	_params = _api.payload['params']
	if _api.response['code'] == 0:
		print("SUCCESS", _params)
	else:
		print("ERROR", _api.response['message'], _params)
	pass


def kraken_call_with_log(_api):
	_params = _api.payload['params']
	_method = _api.payload['method']
	if not _api.response['error']:
		print("SUCCESS", _method, _params)
	else:
		print("ERROR", _api.response['error'], _method, _params)
	pass


def truncate_min(x, decimal):
	if decimal == 0:
		return truncate(x - 1 / (10 ** decimal), decimal)
	else:
		return truncate(x - 1/(10**decimal), decimal)


def truncate_max(x, decimal):
	if decimal == 0:
		return truncate(x + 1 / (10 ** decimal), decimal)
	else:
		return truncate(x + 1/(10**decimal), decimal)


def truncate(x, decimal):
	if decimal == 0:
		return int(round(x, decimal))
	else:
		return round(x, decimal)


def optimize_sell_crypto_com(_crypto_api, _data, _amount, _currency, _reference_crypto_com):
	_price = truncate_max(_data['k'], 5)
	_value = _price * _amount
	_pair = _currency + "_" + _reference_crypto_com

	print("Sell %f %s at %f for %f %s" % (_amount, _currency, _price, _value, _reference_crypto_com))
	_crypto_api.set_command("private/create-order",
							instrument_name = _pair,
							quantity = truncate_min(_amount, 3),
							price = _price,
							side = "SELL",
							type = "LIMIT",
							time_in_force = "GOOD_TILL_CANCEL",
							exec_inst = "POST_ONLY")
	_crypto_api.call_private_api(12)
	call_with_log(_crypto_api)


def sell_crypto_com(_crypto_api, _data, _amount, _currency, _reference_crypto_com):
	_price = _data['k'] * 1.001
	_value = _price * _amount
	print("Sell %f %s at %f for %f %s" % (_amount, _currency, _price, _value, _reference_crypto_com))
	_crypto_api.set_command("private/create-order",
							instrument_name = _currency + "_" + _reference_crypto_com,
							quantity = truncate(_amount, 3),
							side = "SELL",
							type = "MARKET")
	_crypto_api.call_private_api(12)
	call_with_log(_crypto_api)


def get_kraken_asset_balance(_kraken_api, _asset):
	_kraken_api.set_command("/0/public/Assets", asset = _asset)
	_kraken_api.call_public_api()
	_asset_info = *_kraken_api.response['result'],
	_asset_name = _asset_info[0]
	_kraken_api.set_command("/0/private/Balance")
	_kraken_api.call_private_api()
	kraken_call_with_log(_kraken_api)
	_asset_balance = float(_kraken_api.response['result'][_asset_name])
	return _asset_name, _asset_balance



def run(**kwargs):
	_assert_error = "ERROR Missing reference ex: transfer=XLM"
	assert 'transfer' in kwargs, _assert_error
	_assert_error = "ERROR Missing reference ex: reference_crypto_com=USDT"
	assert 'reference_crypto_com' in kwargs, _assert_error
	_assert_error = "ERROR Missing reference ex: reference_kraken=XXBT"
	assert 'reference_kraken' in kwargs, _assert_error
	_assert_error = "ERROR Missing withdraw ex: withdraw=YES"
	assert 'withdraw' in kwargs, _assert_error
	_assert_error = "ERROR Missing withdraw ex: transfer=XLM"
	assert 'withdraw' in kwargs, _assert_error
	_transfer = kwargs['transfer']
	_withdraw = kwargs['withdraw']
	_reference_crypto_com = kwargs['reference_crypto_com']
	_reference_kraken = kwargs['reference_kraken']
	_crypto_api = CryptoApi(path=_PATH)
	_kraken_api = KrakenApi(path=_PATH)

	# GET REF CRYPTO COM
	_list_ref = ['CRO', 'USDT', 'DAI', 'USDC']
	_list_ref.pop(_list_ref.index(_reference_crypto_com))

	_crypto_api.set_command("private/get-account-summary")
	_accounts = _crypto_api.call_private_api(11)
	_continue = True
	for _account in _accounts['result']['accounts']:
		_currency = _account['currency']
		if _currency in _list_ref:
			_amount = _account['available']
			_in_order = _account['order']
			if _amount > 0.01:
				if _in_order > 0:
					_crypto_api.set_command("private/cancel-all-orders", instrument_name=_currency+"_"+_reference_crypto_com)
					_crypto_api.call_private_api(11)
					call_with_log(_crypto_api)

				_crypto_api.set_command("public/get-ticker", instrument_name=_currency+"_"+_reference_crypto_com)
				_tickers = _crypto_api.call_public_api()

				_data = _tickers['result']['data']
				optimize_sell_crypto_com(_crypto_api, _data, _amount, _currency, _reference_crypto_com)
				_order_id = _crypto_api.response['result']['order_id']
				time.sleep(0.5)
				_crypto_api.set_command("private/get-order-detail", order_id=_order_id)
				_crypto_api.call_private_api(11)
				call_with_log(_crypto_api)
				if _crypto_api.response['result']['order_info']['status'] in ["REJECTED", "EXPIRED"]:
					print("ERROR when buying %s " % _currency)
				_continue = False

	if not _continue:
		print("WARNING reference currency not totaly available")
		exit(0)
	_crypto_api.set_command("private/get-account-summary")

	_crypto_api.call_private_api(11)
	_accounts = _crypto_api.response['result']['accounts']

	for _account in _accounts:
		if _account['currency'] == _reference_crypto_com:
			_ref_amount = _account['available']


	##
	with open(str(_PATH)+"/config") as f:
		_config = json.load(f)
	_status_file = str(_PATH)+"/status"
	_ref_amount = 0
	_reference_kraken_balance = 0
	if pathlib.Path(_status_file).exists ():
		with open(_status_file) as f:
			_tmp_conf = json.load(f)
			_ref_amount = _tmp_conf["ref_amount"]
	else:
		_tmp_conf = _config
		_tmp_conf["ref_amount"] = _ref_amount
	###
	print("SUCCESS %f %s available" % (_ref_amount, _reference_crypto_com))
	_status = _tmp_conf["status"]
	_kraken_api.set_command("/0/public/AssetPairs")
	_kraken_api.call_public_api()
	ref = kwargs['reference_kraken']
	for k, v in _kraken_api.response['result'].items():
		_base_currency = v['base']
		_quote_currency = v['quote']
		_pair = k
		_price_decimals = v['pair_decimals']
		_quantity_decimals = v['lot_decimals']
		if _base_currency in _status and not('status' in _status[_base_currency]):
			if _quote_currency == ref:
				if 'status' not in _status[_base_currency]:
					_status[_base_currency]['status'] = _TO_BUY_ON_KRAKEN
					_status[_base_currency]['pair'] = _pair
					_status[_base_currency]['price_decimals'] = _price_decimals
					_status[_base_currency]['quantity_decimals'] = _quantity_decimals
	###
	_crypto_api.set_command("public/get-instruments")
	_instruments = _crypto_api.call_public_api()
	ref = kwargs['reference_crypto_com']
	for v in _instruments['result']['instruments']:
		_base_currency = v['base_currency']
		_quote_currency = v['quote_currency']
		_pair = v['instrument_name']
		_price_decimals = v['price_decimals']
		_quantity_decimals = v['quantity_decimals']
		if _base_currency in _status and not('status' in _status[_base_currency]):
			if _quote_currency == ref:
				if 'status' not in v:
					_status[_base_currency]['status'] = _TO_BUY_ON_CRYPTO_COM
					_status[_base_currency]['pair'] = _pair
					_status[_base_currency]['price_decimals'] = _price_decimals
					_status[_base_currency]['quantity_decimals'] = _quantity_decimals
	###
	###
	_sum_score_kraken = float(0)
	for v in _status.values():
		if v['status'] == _TO_BUY_ON_KRAKEN:
			_sum_score_kraken = _sum_score_kraken + float(v['score'])
	_sum_score = float(sum(i['score'] for i in _status.values()))
	for k, v in _status.items():
		if k == _transfer:
			v['score'] = _sum_score_kraken
		if v['status'] == _TO_BUY_ON_CRYPTO_COM:
			buy_crypto_com(k, v, _crypto_api, _sum_score, _ref_amount, _reference_crypto_com)
			_status[k]['order_id'] = _crypto_api.response['result']['order_id']
			_status[k]['status'] = _IN_ORDER_ON_CRYPTO_COM	
			_continue = False
		elif v['status'] == _IN_ORDER_ON_CRYPTO_COM:
			_crypto_api.set_command("private/get-order-detail", order_id=v['order_id'])
			_crypto_api.call_private_api(11)
			call_with_log(_crypto_api)
			_order_status = _crypto_api.response['result']['order_info']['status']
			if _order_status == "FILLED":
				_status[k]['status'] = _BOUGHT_ON_CRYPTO_COM
				print("SUCCESS when buying %s " % k)
			elif _order_status == "ACTIVE":
				buy_crypto_com(k, v, _crypto_api, _sum_score, _ref_amount, _reference_crypto_com)
				_status[k]['order_id'] = _crypto_api.response['result']['order_id']
			elif _order_status in ["REJECTED", "EXPIRED"]:
				print("ERROR when buying %s " % k)
				buy_crypto_com(k, v, _crypto_api, _sum_score, _ref_amount, _reference_crypto_com)
				_status[k]['order_id'] = _crypto_api.response['result']['order_id']
			_continue = False
		elif v['status'] == _BOUGHT_ON_CRYPTO_COM:

			_address = ""
			if _withdraw == "YES":
				_memo = ""
				if "kraken_memo" in v:
					_memo = v['kraken_memo']
					_address = v['kraken_address']
				else:
					_address = v['ledger_address']
				_crypto_api.set_command("private/get-account-summary", currency=k)
				_crypto_api.call_private_api(11)

				_amount = _crypto_api.response['result']['accounts'][0]['available']
				if _amount > 0.1:
					_crypto_api.set_command("private/create-withdrawal", currency=k, amount=_amount, address=_address, address_tag=_memo)
					_crypto_api.call_private_api(-1)
					call_with_log(_crypto_api)
					if _crypto_api.response['code'] == 0:
						print("SUCCES WITHDRAW of %s to %s " % (k, _address))
						v['status'] = _WITHDREW
					else:
						print("ERROR NEED TO WITHDRAW %s MANNUALLY to %s " % (k, _address))
				else:
					v['status'] = _WITHDREW
			else:
				print("NEED TO WITHDRAW %s MANNUALLY to %s " % (k, _address))

	if not _continue:
		print("WARNING currency not bought yet on crypto.com")
		_tmp_conf["status"] = _status
		with open(str(_PATH) + "/status", 'w') as f:
			json.dump(_tmp_conf, f)
		exit(0)

	#GET XLM BALANCE

	_asset_name, _transfer_balance = get_kraken_asset_balance(_kraken_api, _transfer)
	_sum_score_kraken = _status[_transfer]['score']
	print('SUCCESS %s balance = %s' % (_transfer, _transfer_balance))
	_transfered = False
	if "transfered" in _tmp_conf:
		_transfered = _tmp_conf["transfered"]
		_sum_score_kraken = _tmp_conf["kraken_score"]
	else:
		_tmp_conf["kraken_score"] = _sum_score_kraken
	if float(_transfer_balance) > 0 and not _transfered:
		_tmp_conf["transfered"] = True
		_pair = _status[_asset_name]['pair']
		_price_decimals = _kraken_api.response['result'][_asset_name]['decimals']
		_kraken_api.set_command("/0/public/Ticker", pair = _pair)
		_kraken_api.call_public_api()
		_price = _kraken_api.response['result'][_pair]['a'][0]
		_price_trunc = truncate_max(float(_price), _price_decimals)
		_format = "{0:.%sf}" % _price_decimals
		_price_format = _format.format(_price_trunc)
		if _status[_asset_name]['status'] == _IN_ORDER_ON_KRAKEN:
			_txid = _status[_asset_name]['order_id']
			_kraken_api.set_command("/0/private/QueryOrders", txid = _txid)
			_kraken_api.call_private_api()
			_order_status = _kraken_api.response['result'][_txid]['status']
			if _order_status == "open":
				_kraken_api.set_command("/0/private/CancelOrder", txid=_status[_asset_name]['order_id'])
				_kraken_api.call_private_api()
				kraken_call_with_log(_kraken_api)
			elif _order_status == "close":
				_kraken_api.set_command("/0/private/CancelOrder", txid=_status[_asset_name]['order_id'])
				_kraken_api.call_private_api()
				kraken_call_with_log(_kraken_api)
				_status[_asset_name]['status'] = _SOLD_ON_KRAKEN
				_status[_transfer]['score'] = 0
			else:
				print("ERROR %s when SELLING %s " % (_order_status, _asset_name))
		elif 'status' not in _status[_asset_name] or _status[_asset_name]['status'] == _TO_BUY_ON_KRAKEN:
			_kraken_api.set_command("/0/private/AddOrder", ordertype="limit", pair=_pair, type='sell', volume=_transfer_balance, price=_price_format)
			_kraken_api.call_private_api()
			kraken_call_with_log(_kraken_api)
			_status[_asset_name]['status'] = _IN_ORDER_ON_KRAKEN
			_txid = _kraken_api.response['result']['txid'][0]
			_status[_asset_name]['order_id'] = _txid
	elif _transfered:
		print("SUCCESS %s converted to %s on kraken" % (_transfer, _reference_kraken))
	else:
		_continue = False
	if not _continue:
		print("WARNING fund not transferred to kraken")
		_tmp_conf["status"] = _status
		with open(str(_PATH) + "/status", 'w') as f:
			json.dump(_tmp_conf, f)
		exit(0)
	# ehck if _reference_ kraken setup

	_asset_name, _reference_kraken_balance = get_kraken_asset_balance(_kraken_api, _reference_kraken)

	if "ref_kraken_balance" in _tmp_conf:
		_reference_kraken_balance = _tmp_conf["ref_kraken_balance"]
	else:
		_tmp_conf["ref_kraken_balance"] = _reference_kraken_balance
	print("SUCCESS %f %s available" % (_reference_kraken_balance, _reference_kraken))
	if "ref_kraken_balance" in _tmp_conf:
		_reference_kraken_balance = _tmp_conf["ref_kraken_balance"]
	else:
		_tmp_conf["ref_kraken_balance"] = _reference_kraken_balance


	for k, v in _status.items():
		if v['status'] in[_TO_BUY_ON_KRAKEN, _SOLD_ON_KRAKEN]:
			_status[k] = buy_kraken(k, v, _kraken_api, _sum_score_kraken, _reference_kraken_balance, _reference_kraken)
			_continue = False
		elif v['status'] == _IN_ORDER_ON_KRAKEN:
			_txid = _status[k]['order_id']
			_kraken_api.set_command("/0/private/QueryOrders", txid = _txid)
			_kraken_api.call_private_api()
			_order_status = _kraken_api.response['result'][_txid]['status']
			if _order_status == "closed":
				_status[k]['status'] = _BOUGHT_ON_KRAKEN
				print("SUCCESS when buying %s " % k)
			elif _order_status == "open":
				_kraken_api.set_command("/0/private/CancelOrder", txid=_status[k]['order_id'])
				_kraken_api.call_private_api()
				kraken_call_with_log(_kraken_api)
				_status[k] = buy_kraken(k, v, _kraken_api, _sum_score_kraken, _reference_kraken_balance, _reference_kraken)
			else:
				print("ERROR %s when BUYING %s " % (_order_status, k))
				_status[k] = buy_kraken(k, v, _kraken_api, _sum_score_kraken, _reference_kraken_balance, _reference_kraken)

			_continue = False
		elif v['status'] == _BOUGHT_ON_KRAKEN:
			if _withdraw == "YES":
				_asset_name, _amount = get_kraken_asset_balance(_kraken_api, k)
				_address = v['ledger_address']
				_key = v['key']
				_kraken_api.set_command("/0/private/Withdraw", asset=k, amount=_amount, key=_key)
				_kraken_api.call_private_api()
				kraken_call_with_log(_kraken_api)
				if not _kraken_api.response['error']:
					print("SUCCES WITHDRAW of %s to %s " % (k, _address))
					v['status'] == _WITHDREW
				else:
					print("ERROR NEED TO WITHDRAW %s MANNUALLY to %s " % (k, _address))
			else:
				print("NEED TO WITHDRAW %s MANNUALLY to %s " % (k, _address))

	_tmp_conf["status"] = _status
	with open(str(_PATH) + "/status", 'w') as f:
		json.dump(_tmp_conf, f)


if __name__ == "__main__":
	try:
		_input = (arg.split('=') for arg in sys.argv[1:])
		run(**dict(_input))
	except AssertionError as e:
		print(e)
		exit(1)
