import stock_price_api.config as config
import json
import time
import random
from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
from stock_price_api.redis_config import REDIS_HOST, REDIS_PORT
import redis

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

def get_market_data(message):
	parsedMessage = {
		"DataType": message["DataType"],
		"Content": json.loads(message["Content"])
	}
	# messages.append(parsedMessage)
	symbol = parsedMessage["Content"]["Symbol"]
	serialized_message = json.dumps(parsedMessage)
	redis_client.hset(f"stock:{symbol}", key="data", value=serialized_message)
	redis_client.publish(f"stock:{symbol}:updates", serialized_message)

def getError(error):
	print(error)
	
def get_data_stream():
	selected_channel = "X-TRADE:ALL"
	mm = MarketDataStream(config, MarketDataClient(config))
	mm.start(get_market_data, getError, selected_channel)
	message = None
	while message != "exit()":
		message = input(">> ")
		if message is not None and message != "" and message != "exit()":
			mm.swith_channel(message)


def simulate_get_data():
    with open('stock_price_api/data.json', 'r') as file:
        current_data = json.load(file)
    while True:
        sorted_stocks = sorted(current_data, key=lambda x: x["Content"]["TotalVol"], reverse=True)
        num_to_update = random.randint(20, 100)
        stocks_to_update = random.choices(
            sorted_stocks,
            weights=[stock["Content"]["TotalVol"] for stock in sorted_stocks],
            k=num_to_update
        )
        
        for stock in stocks_to_update:
            content = stock["Content"]
            price_change = content["LastPrice"] * random.uniform(-0.02, 0.02)
            new_price = round(content["LastPrice"] + price_change, -2) 
            new_price = min(max(new_price, content["Floor"]), content["Ceiling"])
            volume_change = random.randint(100, 10000)
            new_total_vol = content["TotalVol"] + volume_change
            content["Change"] = round(new_price - content["RefPrice"], -2)
            content["RatioChange"] = round((content["Change"] / content["RefPrice"]) * 100, 2)
            content["Highest"] = max(content["Highest"], new_price)
            content["Lowest"] = min(content["Lowest"], new_price)
            content["LastPrice"] = new_price
            content["TotalVol"] = new_total_vol
            content["Time"] = time.strftime("%H:%M:%S")
            symbol = content['Symbol']
            serialized_message = json.dumps(stock)
            redis_client.hset(f"stock:{symbol}", key="data", value=serialized_message)
            redis_client.publish(f"stock:{symbol}:updates", serialized_message)
        
        time.sleep(1)