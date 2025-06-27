from flask import Blueprint, jsonify
from utils.utils import get_n_nearest_workdays, convertTradingTimeToString, ratioChange, generate_intervals
from stock_price_api.req_res import md_get_intraday_OHLC, md_get_daily_index
from stock_price_api.redis_config import REDIS_HOST, REDIS_PORT
import redis
from datetime import datetime, timedelta
import json

vnindex = Blueprint('vnindex', __name__)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

@vnindex.route("/")
def getVNIndex():
    now = datetime.now()
    if now.hour < 9 or (now.hour == 9 and now.minute <= 3):
        today = get_n_nearest_workdays(reference_date=datetime.now() - timedelta(days=1))[0]
    else:
        today = get_n_nearest_workdays(reference_date=datetime.now())[0]
    data = md_get_intraday_OHLC('VNINDEX', today, today)["data"]
    # ratioChange = md_get_daily_index(today, today)["data"][0]["RatioChange"]
    parsed_data = [[convertTradingTimeToString(item["TradingDate"], item["Time"]), item["Value"]] for item in data]
    response = jsonify(parsed_data)
    return response

@vnindex.route("/month")
def getVNIndexMonth():
    key = "vnindex-month"
    if redis_client.exists(key):
        data = json.loads(redis_client.get(key))
        response = jsonify(data)
    else:
        interval = generate_intervals(1)[0]
        data = md_get_daily_index(interval[0], interval[1])["data"]
        # ratioChange = md_get_daily_index(today, today)["data"][0]["RatioChange"]
        parsed_data = [[item["TradingDate"], item["IndexValue"]] for item in data]
        redis_client.set(key, json.dumps(parsed_data))
        response = jsonify(parsed_data)
    return response

@vnindex.route("/week")
def getVNIndexWeek():
    key = "vnindex-week"
    if redis_client.exists(key):
        data = json.loads(redis_client.get(key))
        response = jsonify(data)
    else:
        dates = get_n_nearest_workdays(n=7)
        start = dates[len(dates) - 1]
        end = dates[0]
        data = md_get_intraday_OHLC('VNINDEX', start, end)["data"]
        parsed_data = [[convertTradingTimeToString(item["TradingDate"], item["Time"]), item["Value"]] for item in data]
        redis_client.set(key, json.dumps(parsed_data))
        response = jsonify(parsed_data)
    return response

@vnindex.route("/change")
def getVNIndexChange():
    dates = get_n_nearest_workdays(n=30)
    start = dates[len(dates) - 1]
    end = dates[0]
    daily_index = md_get_daily_index(start, end)["data"]
    ratioChanges = {
         '1-day':  float(daily_index[0]["RatioChange"]),
         '1-week': ratioChange(float(daily_index[6]["IndexValue"]), float(daily_index[0]["IndexValue"])),
         '1-month': ratioChange(float(daily_index[len(daily_index) - 1]["IndexValue"]), float(daily_index[0]["IndexValue"]))
    }

    return jsonify(ratioChanges)