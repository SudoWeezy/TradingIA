from Cryptocom.custom_api import CustomApi as CryptoApi
from Kraken.custom_api import CustomApi as KrakenApi
import json
import sys
import pathlib
import time
import copy

_PATH = pathlib.Path(__file__).parent.absolute()
_TIME_BETWEEN_ORDER = 10
_EXIT = 42


def run(**kwargs):
	_assert_error = "ERROR Missing reference ex: reference=EUR"
	assert 'reference' in kwargs, _assert_error
	_assert_error = "ERROR Missing exchange ex: exchange=Kraken"
	assert 'exchange' in kwargs, _assert_error
	_assert_error = "ERROR Missing exchange ex: config=config_kraken"
	assert 'config' in kwargs, _assert_error

	_exchange = kwargs['exchange']
	_ref = kwargs['reference']
	_config = kwargs['config']
	if _exchange == "Kraken":
		_api = KrakenApi(path=_PATH)

	elif _exchange == "Cryptocom":
		_api = CryptoApi(path=_PATH)
	else:
		print("ERROR exchange = %s not defined." % _exchange)
		exit(1)

	_config_file = str(_PATH)+"/" + _config
	
	_assert_error = "ERROR Path = %s not defined." % _config_file
	assert pathlib.Path(_config_file).exists(), _assert_error

	with open(_config_file) as f:
		_config = json.load(f)

	_status = _config["status"]
	_status = _api.setup(_status, _ref)
	dump_status(_status, _exchange)
	_score = 0

	for k, v in _status.items():
		if v['exchange'] == _api.NAME:
			_status[k]['action'] = _api.TO_BUY
			_score = _score + v['score']

	_ref, _ref_amount = _api.get_balance(_ref)

	assert _ref_amount > 10, "ERROR REF AMOUNT %s to low %d " % (_api.NAME, _ref_amount)

	while _status != {}:
		_status = action_on_api(_api, _status, _ref_amount, _score)
		dump_status(_status, _exchange)
		time.sleep(_TIME_BETWEEN_ORDER)


def dump_status(_status, _exchange):
	print("DUMP STATUS")
	_status_file = str(_PATH) + "/status_" + _exchange
	with open(_status_file, 'w') as f:
		json.dump(_status, f)

def action_on_api(_api, _status, _ref_amount, _score_total):
	print("ACTION ON %s " % _api.NAME)
	_tmp_status = copy.deepcopy(_status)
	for k, v in _tmp_status.items():
		if v['exchange'] == _api.NAME and v['score'] > 0:
			_score = v['score']
			_amount = _score / _score_total * _ref_amount
			_status = flow_status(_api, _status, v, k, _amount)
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
		print("vwithdraw %s " % (v['withdraw']))
		if v['withdraw'] == "YES":
			_address = v['address']
			_memo = ""
			if "memo" in v:
				_memo = v['memo']
				_api.withdraw(k, _address, _memo)
		else:
			print("WARNING %s needs to be withdraw manually from %s" % (k, _api.NAME))
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
		exit(_EXIT)
