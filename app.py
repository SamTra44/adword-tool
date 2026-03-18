from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os

app = Flask(__name__, static_folder="static")
CORS(app)

# --- HIDDEN CONFIG ---
API_KEY = os.environ.get("SMM_API_KEY", "877f4a9fcf5d5770b86f97867beea5bc")
API_URL = "https://honestsmm.com/api/v2"
SERVICE_ID = "1554"
# ---------------------

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/place-order", methods=["POST"])
def place_order():
    data = request.json
    link = data.get("link", "").strip()
    quantity = data.get("quantity", 0)

    if not link or "facebook.com" not in link:
        return jsonify({"error": "Valid Facebook link required"}), 400
    if not (20 <= int(quantity) <= 5000):
        return jsonify({"error": "Quantity must be 20-5000"}), 400

    try:
        resp = requests.post(API_URL, data={
            "key": API_KEY,
            "action": "add",
            "service": SERVICE_ID,
            "link": link,
            "quantity": quantity
        }, timeout=15)
        result = resp.json()

        # Hide pricing/charge info, only return order ID or clean error
        if "order" in result:
            return jsonify({"order": result["order"]})
        elif "error" in result:
            err = result["error"].lower()
            if "balance" in err or "fund" in err or "credit" in err or "insufficient" in err:
                return jsonify({"error": "BALANCE_LOW"})
            return jsonify({"error": "Order could not be placed. Please try again."})
        else:
            return jsonify({"error": "Unexpected response. Try again."})
    except Exception as e:
        return jsonify({"error": "Connection failed. Please try again."}), 500

@app.route("/check-balance", methods=["GET"])
def check_balance():
    try:
        resp = requests.post(API_URL, data={
            "key": API_KEY,
            "action": "balance"
        }, timeout=10)
        result = resp.json()
        if "balance" in result:
            bal = float(result["balance"])
            return jsonify({"ok": True, "low": bal < 50})
        return jsonify({"ok": False})
    except:
        return jsonify({"ok": False})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
