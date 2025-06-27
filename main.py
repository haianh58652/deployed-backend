import threading
from flask import Flask
import json
from flask_socketio import SocketIO
from flask_cors import CORS
from vnindex.routes import vnindex
from details.routes import details
from chatbot.routes import chatbot
from stock_price_api.stream import get_data_stream, simulate_get_data
from stock_price_api.redis_config import REDIS_HOST, REDIS_PORT
from predictions.routes import predictions, predictListSymbol
import redis
import os
app = Flask(__name__)
app.register_blueprint(vnindex, url_prefix="/vnindex")
app.register_blueprint(details, url_prefix="/details")
app.register_blueprint(predictions, url_prefix="/predictions")
app.register_blueprint(chatbot, url_prefix="/chatbot")
CORS(app)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")
redis_client = redis.Redis.from_url("rediss://default:ASvQAAIjcDExZTE5Yzc1MmUwY2I0NDM4YWE3N2FkYWI4MDY5MWQ5ZXAxMA@obliging-warthog-11216.upstash.io:6379")

def listen_data_stream():
    pubsub = redis_client.pubsub()
    pubsub.psubscribe("stock:*:updates")

    for message in pubsub.listen():
        if message['type'] == 'pmessage':
            data = json.loads(message['data'])
            socketio.emit('stock_update', data)

@socketio.on("connect")
def handle_connect():
    print("Client connected!!!")
    data = []
    keys = redis_client.keys('stock:*')
    for key in keys:
        value = redis_client.hget(key, "data")
        if value:
            decoded_value = value.decode('utf-8')
            parsed_value = json.loads(decoded_value)
            data.append(parsed_value)
    socketio.emit('connect_update', data)

markets = ["HOSE", "HOSE", "HOSE", "HOSE", "HOSE", "HOSE", "HOSE", "HOSE", "UPCOM"]
symbols = ["VCI", "SSI", "HDB", "VPB", "BID", "VCB", "FPT", "CMG", "MFS"]
listen_market_thread = threading.Thread(target=listen_data_stream, daemon=True)
listen_market_thread.start()

market_thread = threading.Thread(target=get_data_stream, daemon=True)
# market_thread = threading.Thread(target=simulate_get_data, daemon=True)
market_thread.start()

predictions_thread = threading.Thread(target=predictListSymbol, daemon=True, args=(symbols, markets))
predictions_thread.start()
if __name__ == "__main__":
    # md_get_daily_index()
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
	
