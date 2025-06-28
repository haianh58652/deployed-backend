import threading
from flask import Flask, redirect, request
import json
from flask_socketio import SocketIO
from flask_cors import CORS
from vnindex.routes import vnindex
from details.routes import details
from chatbot.routes import chatbot
from stock_price_api.stream import get_data_stream, simulate_get_data
from stock_price_api.redis_config import REDIS_HOST, REDIS_PORT
from predictions.routes import predictions, predictListSymbol
from werkzeug.middleware.proxy_fix import ProxyFix
import redis
import os
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Register blueprints
app.register_blueprint(vnindex, url_prefix="/vnindex")
app.register_blueprint(details, url_prefix="/details")
app.register_blueprint(predictions, url_prefix="/predictions")
app.register_blueprint(chatbot, url_prefix="/chatbot")

# Configure CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure SocketIO with proper settings for Render
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',  # Explicitly set async mode
    transports=['websocket'],  # Allow both transports
    engineio_logger=True,  # Enable logging for debugging
    socketio_logger=True   # Enable logging for debugging
)

redis_client = redis.Redis.from_url("rediss://default:ASvQAAIjcDExZTE5Yzc1MmUwY2I0NDM4YWE3N2FkYWI4MDY5MWQ5ZXAxMA@obliging-warthog-11216.upstash.io:6379")

def listen_data_stream():
    pubsub = redis_client.pubsub()
    pubsub.psubscribe("stock:*:updates")
    for message in pubsub.listen():
        if message['type'] == 'pmessage':
            data = json.loads(message['data'])
            socketio.emit('stock_update', data)

@app.before_request
def force_https():
    if not request.is_secure and not app.debug:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)
        
@socketio.on("connect")
def handle_connect(auth=None):
    print("Client connected!!!")
    data = []
    try:
        cursor = '0'
        while cursor != 0:
            cursor, keys = redis_client.scan(cursor=cursor, match='stock:*', count=100)
            for key in keys:
                value = redis_client.hget(key, "data")
                if value:
                    parsed_value = json.loads(value)
                    data.append(parsed_value)
        socketio.emit('connect_update', data)
    except redis.ConnectionError as e:
        print(f"Redis connection error: {e}")
        socketio.emit('connect_update', [])
    except redis.ResponseError as e:
        print(f"Redis response error: {e}")
        socketio.emit('connect_update', [])

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")

 markets = ["HOSE", "HOSE", "HOSE", "HOSE", "HOSE", "HOSE", "HOSE", "HOSE", "UPCOM"]
symbols = ["VCI", "SSI", "HDB", "VPB", "BID", "VCB", "FPT", "CMG", "MFS"]
    
# Start background threads
listen_market_thread = threading.Thread(target=listen_data_stream, daemon=True)
listen_market_thread.start()
    
market_thread = threading.Thread(target=get_data_stream, daemon=True)
market_thread.start()
    
predictions_thread = threading.Thread(target=predictListSymbol, daemon=True, args=(symbols, markets))
predictions_thread.start()
    
port = int(os.environ.get('PORT', 5000))
if __name__ == "__main__":
    # Run with proper configuration for Render
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=port, 
        debug=False,
        allow_unsafe_werkzeug=True
    )
