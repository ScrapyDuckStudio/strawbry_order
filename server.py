"""
Minimal Flask API for Strawberry Orders.
Replaces Streamlit — serves the HTML frontend + JSON API for shared data.
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from database import (
    init_db, verify_user, get_all_users, change_password,
    get_full_order, get_all_full_orders,
    save_order, submit_order, reset_all_orders, reset_apt_order,
    mark_delivered, undeliver_order,
    get_token_for_apt, verify_token,
    get_available_products, set_product_available,
    ALL_PRODUCTS, APARTMENTS, PAYMENT_METHODS, TIME_SLOTS,
)
import os

app = Flask(__name__, static_folder="docs", static_url_path="")
CORS(app)

init_db()


# ── Serve frontend ──
@app.route("/")
def index():
    return send_from_directory("docs", "index.html")


# ── Auth ──
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json or {}
    user = verify_user(data.get("username", ""), data.get("password", ""))
    if user:
        return jsonify({"ok": True, "user": {
            "username": user["username"],
            "role": user["role"],
            "apt_id": user.get("apt_id"),
        }})
    return jsonify({"ok": False, "error": "Wrong credentials"}), 401


@app.route("/api/login/token", methods=["POST"])
def api_token_login():
    data = request.json or {}
    user = verify_token(data.get("token", ""))
    if user:
        return jsonify({"ok": True, "user": {
            "username": user["username"],
            "role": user["role"],
            "apt_id": user.get("apt_id"),
        }})
    return jsonify({"ok": False, "error": "Invalid token"}), 401


# ── Products ──
@app.route("/api/products")
def api_products():
    available = get_available_products()
    return jsonify({
        "all": {pid: info for pid, info in ALL_PRODUCTS.items()},
        "available": available,
    })


@app.route("/api/products/toggle", methods=["POST"])
def api_toggle_product():
    data = request.json or {}
    pid = data.get("product")
    enabled = data.get("enabled", True)
    if pid not in ALL_PRODUCTS:
        return jsonify({"ok": False, "error": "Unknown product"}), 400
    set_product_available(pid, enabled)
    return jsonify({"ok": True})


# ── Orders ──
@app.route("/api/orders")
def api_all_orders():
    orders = get_all_full_orders()
    return jsonify({"orders": orders})


@app.route("/api/orders/<int:apt_id>")
def api_get_order(apt_id):
    order = get_full_order(apt_id)
    return jsonify({"order": order})


@app.route("/api/orders/<int:apt_id>/save", methods=["POST"])
def api_save_order(apt_id):
    data = request.json or {}
    lines = data.get("lines", {})
    delivery_time = data.get("delivery_time", "")
    payment_method = data.get("payment_method", "")
    save_order(apt_id, lines, delivery_time, payment_method)
    return jsonify({"ok": True})


@app.route("/api/orders/<int:apt_id>/submit", methods=["POST"])
def api_submit_order(apt_id):
    data = request.json or {}
    lines = data.get("lines", {})
    delivery_time = data.get("delivery_time", "")
    payment_method = data.get("payment_method", "")
    save_order(apt_id, lines, delivery_time, payment_method)
    submit_order(apt_id)
    return jsonify({"ok": True})


@app.route("/api/orders/<int:apt_id>/deliver", methods=["POST"])
def api_deliver(apt_id):
    mark_delivered(apt_id)
    return jsonify({"ok": True})


@app.route("/api/orders/<int:apt_id>/undeliver", methods=["POST"])
def api_undeliver(apt_id):
    undeliver_order(apt_id)
    return jsonify({"ok": True})


@app.route("/api/orders/<int:apt_id>/reset", methods=["POST"])
def api_reset_order(apt_id):
    reset_apt_order(apt_id)
    return jsonify({"ok": True})


@app.route("/api/orders/reset-all", methods=["POST"])
def api_reset_all():
    reset_all_orders()
    return jsonify({"ok": True})


# ── Config ──
@app.route("/api/config")
def api_config():
    return jsonify({
        "apartments": APARTMENTS,
        "payment_methods": PAYMENT_METHODS,
        "time_slots": TIME_SLOTS,
    })


# ── Passwords ──
@app.route("/api/passwords", methods=["POST"])
def api_change_passwords():
    data = request.json or {}
    changes = data.get("changes", {})
    changed = 0
    for username, new_pwd in changes.items():
        if new_pwd.strip():
            change_password(username, new_pwd.strip())
            changed += 1
    return jsonify({"ok": True, "changed": changed})


# ── Users list (for super admin) ──
@app.route("/api/users")
def api_users():
    users = get_all_users()
    return jsonify({"users": users})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
