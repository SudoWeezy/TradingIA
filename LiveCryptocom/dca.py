from api import Api
import json
import sys
import pathlib
_PATH = pathlib.Path(__file__).parent.absolute()

def get_list_pair(_api, _list_currencies, _reference):
	_list_pair = []
	_list_instr = []
	_api.set_command("public/get-instruments")
	_instruments = _api.call_public_api()
	for _instrument in _instruments['result']['instruments']:
		if _instrument['base_currency'] in _list_currencies:
			if _instrument['quote_currency'] == _reference:
				_list_pair.append(_instrument['instrument_name'])
				_list_instr.append(_instrument['base_currency'])

	_assert_error = "ERROR " + _reference + "not available for every currency"
	assert len(_list_currencies) == len(_list_pair), _assert_error
	return _list_pair, _list_instr


def withdraw(_api, _list_currencies, _config):
	_api.set_command("private/get-account-summary")
	_accounts = _api.call_private_api(11)
	for _account in _accounts['result']['accounts']:
		_currency = _account['currency']
		if _currency in _list_currencies:
			if _config[_currency]['score'] > 0:
				_amount = _account['available']
				_address = _config[_currency]['address']
				print("withdraw " + _currency + " to " + _address)
				_api.set_command("private/create-withdrawal", 
					currency=_currency, 
					amount=_amount, 
					address=_address)
				call_with_log(_api)			
	pass


def get_ref_amount(_api, _reference):
	_list_ref = ['CRO', 'USDT', 'DAI', 'USDC']
	_list_ref.pop(_list_ref.index(_reference))

	_api.set_command("private/get-account-summary")
	_accounts = _api.call_private_api(11)

	for _account in _accounts['result']['accounts']:
		_currency = _account['currency']
		if _currency in _list_ref:
			_amount = _account['available']
			if _amount > 0.001:
				_api.set_command("private/create-order",
					instrument_name=_currency+"_"+_reference,
					quantity=("%.3f" % _amount),
					side="SELL",
					type="MARKET")
				call_with_log(_api)

	_api.set_command("private/get-account-summary")
	_accounts = _api.call_private_api(11)

	for _account in _accounts['result']['accounts']:
		if _account['currency'] == _reference:
			return (_account['available'])


def buy(_api, _reference, _list_pair, _list_instr, _config, _ref_amount):
	_api.set_command("public/get-ticker")
	_tickers = _api.call_public_api()
	_sum_score = float(sum(i['score'] for i in _config.values()))
	if _ref_amount > 1:
		for _ticker in _tickers['result']['data']:
			if _ticker['i'] in _list_pair:
				_instr = _list_instr[_list_pair.index(_ticker['i'])]
				_score = float(_config[_instr]['score']) / _sum_score
				_value = _score * _ref_amount / _ticker['a']
				_amount = _value * _ticker['a']
				if _amount > 0:
					print(_value * _ticker['a'])
					print("Buy %f %s at %f for %f %s" % 
						(_value, _instr, _ticker['a'], _amount, _reference))
					_api.set_command("private/create-order", 
						instrument_name=_ticker['i'], 
						notional=("%.3f" % _amount), 
						side="BUY", 
						type="MARKET")
					call_with_log(_api)
	pass


def call_with_log(_api):
	_api.call_private_api(11)
	_params = _api.payload['params']
	if _api.response['code'] == 0:
		print("SUCCESS", _params)
	else:
		print("ERROR", _api.response['message'], _params)
	pass

def run(**kwargs):

	_assert_error = "ERROR Missing reference ex: reference=USDT"
	assert 'reference' in kwargs, _assert_error
	_assert_error = "ERROR Missing withdraw ex: withdraw=YES"
	assert 'withdraw' in kwargs, _assert_error
	_api = Api(path=_PATH)
	_reference = kwargs['reference']
	_withdraw = kwargs['withdraw']

	with open(str(_PATH)+"/config") as f:
		_config = json.load(f)
	_list_currencies = list(_config.keys())

	_list_pair, _list_instr = get_list_pair(_api, _list_currencies, _reference)

	_ref_amount = get_ref_amount(_api, _reference)
	print("ref: %f %s" % (_ref_amount, _reference))
	_assert_error = "ERROR Not enough fund"
	assert float(_ref_amount) > 1, _assert_error

	buy(_api, _reference, _list_pair, _list_instr, _config, _ref_amount)

	if _withdraw == "YES":
		withdraw(_api, _list_currencies, _config)


if __name__ == "__main__":
	try:
		_input = (arg.split('=') for arg in sys.argv[1:])
		run(**dict(_input))
	except AssertionError as e:
		print(e)
		exit(1)
