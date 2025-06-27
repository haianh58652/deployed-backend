from utils.utils import convertTradingTimeToString, generate_intervals, get_n_nearest_workdays
from stock_price_api.req_res import md_get_stock_price, md_get_daily_index, md_get_intraday_OHLC
import json
import redis
from stock_price_api.redis_config import REDIS_HOST, REDIS_PORT
from flask import Blueprint, request, jsonify
import numpy as np
import random
import pandas as pd
redis_client = redis.Redis.from_url("rediss://default:ASvQAAIjcDExZTE5Yzc1MmUwY2I0NDM4YWE3N2FkYWI4MDY5MWQ5ZXAxMA@obliging-warthog-11216.upstash.io:6379")
predictions = Blueprint('predictions', __name__)
import time



def convert_to_datetime(n):
    n = str(n)
    return n[0:4] + "-" + n[4:6] + "-" + n[6:]

def predict(prices_30_days):
    if len(prices_30_days) < 5:
        raise ValueError("Cần ít nhất 5 ngày để dự đoán xu hướng.")
    
    last_prices = prices_30_days[-5:]
    deltas = [last_prices[i+1] - last_prices[i] for i in range(4)]
    avg_delta = sum(deltas) / len(deltas)

    predicted = []
    current_price = prices_30_days[-1]
    for _ in range(7):
        noise = random.uniform(-0.3, 0.3)
        current_price += avg_delta + noise
        predicted.append(round(current_price, 2))

    return predicted

@predictions.route("", methods=['POST'])
def getPredicts():
    data = request.json
    symbol = data.get("symbol").upper()
    market = data.get("market").upper()
    key = f"predict-{symbol}"
    interval = generate_intervals(1)[0]

    if redis_client.exists(key):
        predictions = json.loads(redis_client.get(key))
    else:
        response = md_get_stock_price(symbol, market, interval[0], interval[1])["data"]
        data = [ float(item['ClosePrice']) for item in response]
        predictions = predict(data)
        redis_client.set(key, json.dumps(predictions))
    return jsonify(predictions)

def predictListSymbol(symbols, markets):
    interval = generate_intervals(1)[0]
    for i in range(len(symbols)):
        symbol = symbols[i]
        market = markets[i]
        key = f"predict-{symbol}"

        if not redis_client.exists(key):
            try:
                response = md_get_stock_price(symbol, market, interval[0], interval[1])["data"]
                data = [float(item['ClosePrice']) for item in response]
                predictions = predict(data)
                redis_client.set(key, json.dumps(predictions))
            except:
                print("there is an error")

        time.sleep(1)
    
    key = "vnindex-month"
    data = md_get_daily_index(interval[0], interval[1])["data"]
    # ratioChange = md_get_daily_index(today, today)["data"][0]["RatioChange"]
    parsed_data = [[item["TradingDate"], item["IndexValue"]] for item in data]
    redis_client.set(key, json.dumps(parsed_data))
    time.sleep(1)

    key = "vnindex-week"
    dates = get_n_nearest_workdays(n=7)
    start = dates[len(dates) - 1]
    end = dates[0]
    data = md_get_intraday_OHLC('VNINDEX', start, end)["data"]
    parsed_data = [[convertTradingTimeToString(item["TradingDate"], item["Time"]), item["Value"]] for item in data]
    redis_client.set(key, json.dumps(parsed_data))

    print("Fetch in background complete")
