from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # ✅ This enables CORS for all routes

@app.route("/")
def index():
    return "API is working"

@app.route("/api/test", methods=["GET", "POST", "OPTIONS"])
def test_api():
    if request.method == "OPTIONS":
        return '', 200
    return jsonify({"success": True, "message": "API is working properly!"})
