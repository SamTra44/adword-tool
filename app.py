from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import requests
import os

app = Flask(__name__, static_folder="static")
CORS(app)
app.secret_key = "adword_secret_x9k2m"

# --- CONFIG ---
API_KEY  = os.environ.get("SMM_API_KEY", "877f4a9fcf5d5770b86f97867beea5bc")
API_URL  = "https://honestsmm.com/api/v2"

# Allowed service IDs
ALLOWED_SERVICES = {"1554", "1236"}

# Login
USERNAME = "rozmin"
PASSWORD = "Secure@123"
# --------------

@app.route("/")
def index():
    if not session.get("logged_in"):
        return send_from_directory("static", "login.html")
    return send_from_directory("static", "index.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    if data.get("username") == USERNAME and data.get("password") == PASSWORD:
        session["logged_in"] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid username or password"})

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/place-order", methods=["POST"])
def place_order():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    data       = request.json
    link       = data.get("link", "").strip()
    quantity   = data.get("quantity", 0)
    service_id = str(data.get("service_id", "1554")).strip()

    # Validate service
    if service_id not in ALLOWED_SERVICES:
        return jsonify({"error": "Invalid service selected"}), 400

    if not link or "facebook.com" not in link:
        return jsonify({"error": "Valid Facebook link required"}), 400
    if not (20 <= int(quantity) <= 5000):
        return jsonify({"error": "Quantity must be 20-5000"}), 400

    try:
        resp   = requests.post(API_URL, data={
            "key":      API_KEY,
            "action":   "add",
            "service":  service_id,
            "link":     link,
            "quantity": quantity
        }, timeout=15)
        result = resp.json()

        if "order" in result:
            return jsonify({"order": result["order"]})
        elif "error" in result:
            err = result["error"].lower()
            if any(w in err for w in ["balance","fund","credit","insufficient"]):
                return jsonify({"error": "BALANCE_LOW"})
            return jsonify({"error": "Order could not be placed. Please try again."})
        else:
            return jsonify({"error": "Unexpected response. Try again."})
    except Exception:
        return jsonify({"error": "Connection failed. Please try again."}), 500

@app.route("/check-balance", methods=["GET"])
def check_balance():
    if not session.get("logged_in"):
        return jsonify({"ok": False}), 401
    try:
        resp   = requests.post(API_URL, data={"key": API_KEY, "action": "balance"}, timeout=10)
        result = resp.json()
        if "balance" in result:
            bal = float(result["balance"])
            return jsonify({"ok": True, "low": bal < 50})
        return jsonify({"ok": False})
    except Exception:
        return jsonify({"ok": False})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
