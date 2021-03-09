from Cryptocom.custom_api import CustomApi as CryptoApi
from Kraken.custom_api import CustomApi as KrakenApi
import json
import sys
import pathlib
import time


_PATH = pathlib.Path(__file__).parent.absolute()
_TIME_BETWEEN_ORDER = 300
_EXIT = 420


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
		if v['exchange'] == _kraken_api.NAME:
			_status[k]['action'] = _kraken_api.TO_BUY
			_score_kraken = _score_kraken + v['score']
		elif v['exchange'] == _crypto_api.NAME:
			_status[k]['action'] = _crypto_api.TO_BUY
			_score_crypto = _score_crypto + v['score']
		else:
			print("ASSET NOT AVAILABLE", k)

	_score_total = _score_crypto + _score_kraken
	_ref_amount_crypto_com = float(0)
	_ref_amount_kraken = float(0)

	_ref_amount_crypto_com = _crypto_api.get_ref_amount(_ref_crypto_com)
	assert _ref_amount_crypto_com > 1, "ERROR REF AMOUNT CRYPTO_COM to low"

	print("BUYING CURRENCY FOR TRANSFER")
	while _transfer in _status:
		time.sleep(_TIME_BETWEEN_ORDER)
		_status = transfer_from_crypto_to_kraken(_crypto_api, _transfer, _status, _ref_amount_crypto_com, _score_kraken, _score_total)

	dump_status(_status)

	_asset_name, _prev_amount = _kraken_api.get_balance(_transfer)
	_amount = _prev_amount
	print("WARNING WAITING FOR TRANSFER")
	while _prev_amount == _amount:
		time.sleep(_TIME_BETWEEN_ORDER)
		_asset_name, _amount = _kraken_api.get_balance(_transfer)

	_ref_amount_kraken = _kraken_api.get_ref_amount(_transfer, _status, _ref_kraken)
	assert _ref_amount_kraken > 0.001, "ERROR REF AMOUNT KRAKEN to low"
	while _status != {}:
		_status = action_on_crypto_com(_crypto_api, _transfer, _status, _ref_amount_crypto_com, _score_total)
		_status = action_on_kraken(_kraken_api, _transfer, _status, _ref_amount_kraken, _score_kraken)
		dump_status(_status)
		time.sleep(_TIME_BETWEEN_ORDER)


def dump_status(_status):
	print("DUMP STATUS")
	_status_file = str(_PATH) + "/status"
	with open(_status_file, 'w') as f:
		json.dump(_status, f)


def transfer_from_crypto_to_kraken(_crypto_api, _transfer, _status, _ref_amount_crypto_com, _score_kraken, _score_total):
	print("TRANSFER %s FROM CRYPTO.COM TO KRAKEN" % _transfer)
	v = _status[_transfer]
	k = _transfer
	_amount = _score_kraken / _score_total * _ref_amount_crypto_com
	_status = flow_status(_crypto_api, _status, v, k, _amount)
	return _status


def action_on_crypto_com(_crypto_api, _transfer, _status, _ref_amount_crypto_com, _score_total):
	print("ACTION ON CRYPTO.COM")
	for k, v in _status.items():
		if v['exchange'] == _crypto_api.NAME and v['score'] > 0:
			_score = v['score']
			_amount = _score / _score_total * _ref_amount_crypto_com
			_status = flow_status(_crypto_api, _status, v, k, _amount)
	return _status


def action_on_kraken(_kraken_api, _transfer, _status, _ref_amount_kraken, _score_kraken):
	print("ACTION ON KRAKEN")
	for k, v in _status.items():
		if v['exchange'] == _kraken_api.NAME and v['score'] > 0:
			_score = v['score']
			_amount = _score / _score_kraken * _ref_amount_kraken
			_status = flow_status(_kraken_api, _status, v, k, _amount)
	return _status


def flow_status(_api, _status, v, k, _amount):
	_action = v['action']
	_pair = v['pair']
	print("FLOW STATUS", v, _pair, _amount)
	if _action == _api.TO_BUY:

		_check = _api.buy(_amount, _pair)
		if _check == _api.SUCCESS:
			_status[k]['action'] = _api.BOUGHT
		elif _check != _api.ERROR:
			_status[k]['tx_id'] = _check
			_status[k]['amount'] = _amount
			_status[k]['action'] = _api.IN_ORDER
	elif _action == _api.IN_ORDER:
		_tx_id = v['tx_id']
		_amount = v['amount']
		_check = _api.check_order(_tx_id, _amount, _pair)
		if _check == _api.SUCCESS:
			_status[k]['action'] = _api.BOUGHT
		elif _check != _api.ERROR:
			_status[k]['tx_id'] = _check
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
