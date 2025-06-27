import stock_price_api.config as config
from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_fc_data import model

			
client = MarketDataClient(config)
def md_get_stock_price(symbol, market, fromDate, toDate):
	return client.daily_stock_price(config, model.daily_stock_price (symbol, fromDate, toDate, 1, 100, market))

def md_get_securities_details(symbol, market):
    req = model.securities_details(market, symbol, 1, 100)
    return client.securities_details(config, req)

def md_get_daily_index(fromDate, toDate):
    return client.daily_index(config, model.daily_index( '100', 'VNINDEX', fromDate, toDate, 1, 100, '', ''))

def md_get_intraday_OHLC(symbol, fromDate, toDate):
    result = client.intraday_ohlc(config, model.intraday_ohlc(symbol, fromDate, toDate, 1, 1000, True, 1))
    return result