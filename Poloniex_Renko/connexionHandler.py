
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

url = "https://poloniex.com/public?"

parameters = {
  'command':'returnChartData',
  'currencyPair':'BTC_ETH',
  'start':'1410158341',
  'end':'999999999999',
  'period':'14400'
}

session = Session()

try:
  response = session.get(url, params=parameters)
  print(response)
  print(dir(response))
except (ConnectionError, Timeout, TooManyRedirects) as e:
  print(e)
