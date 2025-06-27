from flask import Blueprint, request, jsonify
from utils.utils import get_n_nearest_workdays
from stock_price_api.req_res import md_get_stock_price, md_get_securities_details, md_get_intraday_OHLC
from stock_price_api.redis_config import REDIS_HOST, REDIS_PORT
import redis
import json
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
from datetime import datetime, timedelta
details = Blueprint('details', __name__)

@details.route("", methods=['POST'])
def getStockDetails():
    key = "stock-details"
    data = request.json
    symbol = data.get("symbol")
    market = data.get("market")
    date = get_n_nearest_workdays(datetime.now() - timedelta(days=1))[0]

    if redis_client.exists(key):
        response = json.loads(redis_client.get(key))
    else:
        response = md_get_stock_price(symbol, market, date, date)["data"]
        redis_client.set(key, json.dumps(response))
        
    data = list(filter(lambda item: symbol.lower() == item["Symbol"].lower(), response))
    company_response = md_get_securities_details(symbol, market)["data"]

    parsedData = {
        "Symbol": data[0]["Symbol"],
        "CurrentPrice": data[0]["ClosePrice"],
        "OpenPrice": data[0]["OpenPrice"],
        "HighestPrice": data[0]["HighestPrice"],
        "LowestPrice": data[0]["LowestPrice"],
        "CompanyName": company_response[0]["RepeatedInfo"][0]["SymbolName"],
        "EngCompanyName": company_response[0]["RepeatedInfo"][0]["SymbolEngName"],
        "CeilingPrice": data[0]["CeilingPrice"],
        "FloorPrice": data[0]["FloorPrice"],
        "RefPrice": data[0]["RefPrice"]
    }
    return jsonify(parsedData)

@details.route("/intraday", methods=['POST'])
def getIntradayStockPrice():
    data = request.json
    symbol = data.get("symbol")

    today = get_n_nearest_workdays(datetime.now() - timedelta(days=1))[0]
    data = md_get_intraday_OHLC(symbol, today, today)["data"]

    return jsonify(data)