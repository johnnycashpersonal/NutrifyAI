from selenium import webdriver
from user import exchange_code_for_token, add_item_to_cart
import app
from flask import Flask, request, jsonify, redirect, session

@app.route("/add-to-cart", methods=["POST"])
def add_to_cart_route():
    data = request.json
    items = data.get("items", [])  # e.g. ["0001111019270", "0001111060903"]
    if not items:
        return jsonify({"success": False, "error": "No items provided"}), 400

    # Retrieve user token from session
    user_token = session.get("kroger_user_token")
    if not user_token:
        return jsonify({"success": False, "error": "User not logged in to Kroger"}), 401

    # For each item (assume it's a UPC), call add_item_to_cart
    success_list = []
    for upc in items:
        success = add_item_to_cart(user_token, upc, quantity=1, modality="PICKUP")
        success_list.append(success)

    if all(success_list):
        return jsonify({"success": True, "message": f"Added {len(items)} items to Kroger cart"})
    else:
        return jsonify({"success": False, "error": "One or more items failed to add."})

