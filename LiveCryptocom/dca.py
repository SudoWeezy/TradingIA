from api import Api
import json
import sys


def check_reference():
	pass


def withdraw():
	pass


def buy():
	pass


def run(**kwargs):

	_assert_error = "Missing inputs ex: reference=USDT"
	assert 'reference' in kwargs, _assert_error

	_reference = kwargs['reference']
	_api = Api()
	_api.set_command("public/get-instruments")
	_instruments = _api.call_public_api()
	# TODO config en input
	with open("config") as f:
		_config = json.load(f)
	_list_currencies = list(_config.keys())
	_list_pair = []
	for _instrument in _instruments['result']['instruments']:
		if _instrument['base_currency'] in _list_currencies:
			if _instrument['quote_currency'] == _reference:
				_list_pair.append(_instrument['instrument_name'])

	_assert_error = kwargs['reference'] + " not available for every currency"
	assert len(_list_currencies) == len(_list_pair), _assert_error

	_api.set_command("public/get-ticker")
	_tickers = _api.call_public_api()
	for _ticker in _tickers['result']['data']:
		if _ticker['i'] in _list_pair:
			# TODO Calculate Buy amount
			print("Buy %s at %f %s" % (_ticker['i'], _ticker['a'], _reference))
			# TODO Ordre d'achat si possible Market amount

	for _currency in _list_currencies:
		# TODO  get amount currency, withdraw si cout < 1%
		print("withdraw " + _currency + " to " + _config[_currency]['address'])


if __name__ == "__main__":
	try:
		assert len(sys.argv) % 2 == 0, "Missing inputs key=value or not even"
		_input = (arg.split('=') for arg in sys.argv[1:])
		run(**dict(_input))
	except AssertionError as e:
		print(e)
		exit(1)
