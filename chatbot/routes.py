from flask import Blueprint, request, jsonify
import time

chatbot = Blueprint('chatbot', __name__)
@chatbot.route("", methods=['POST'])
def getAnswer():
    time.sleep(2)
    answer = "You have exceeded your quota of tokens for this billing period. Please upgrade your plan or wait until your quota resets."
    return jsonify(answer)
