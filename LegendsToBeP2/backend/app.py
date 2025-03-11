from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
from recipe_handler import fetch_recipe
from store_handler import fetch_ingredient_prices
from user import exchange_code_for_token, add_item_to_cart
from dotenv import load_dotenv
from data import Database
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "some-secret-key"  # Required for session management

# Enable CORS with credentials
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])  # Replace with your frontend URL

# Configure session cookies for cross-origin requests
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True  # Ensure cookies are only sent over HTTPS

# Kroger API constants
CLIENT_ID = "nutrifai-243261243034242e644175722e4a4c397a4e507a454732506e594e366576617532756c356b4741754c48746c31634a59564b784d4f2e364e7743462e3423701595089688646"
REDIRECT_URI = "http://127.0.0.1:5000/callback"
AUTH_URL = "https://api.kroger.com/v1/connect/oauth2/authorize"  # Add this line

@app.route("/test", methods=["GET", "POST"])
def test():
    return jsonify({"message": "CORS test endpoint"}), 200

@app.route("/")
def home():
    return jsonify({"message": "Welcome to Nutrify AI!"})

@app.route("/generate-recipe", methods=["POST"])
def generate_recipe():
    data = request.json
    user_prompt = data.get("description", "")
    recipe = fetch_recipe(user_prompt)
    return jsonify(recipe)

@app.route("/save-recipe", methods=["POST"])
def save_recipe():
    data = request.json
    print(data)
    
    if not data or 'recipe' not in data:
        return jsonify({
            'success': False,
            'error': 'Invalid request: missing recipe data'
        }), 400
    
    recipe_data = data['recipe']
    
    required_fields = ['name', 'ingredients', 'instructions']
    if not all(field in recipe_data for field in required_fields):
        return jsonify({
            'success': False,
            'error': 'Invalid recipe: missing required fields'
        }), 400
    
    try:
        db = Database()
        
        db.insert_recipe(data)
        
        return jsonify({
            'success': True,
            'message': 'Recipe saved successfully',
            'recipe_id': str(recipe_id)
        })
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error saving recipe: {str(e)}")
        
        # Return error response
        return jsonify({
            'success': False,
            'error': 'Failed to save recipe'
        }), 500

@app.route("/get-past", methods=["POST"])
def get_past_recipes():
    print("getting past...")
    db = Database()

    recipes = db.get_all_recipes()
    print(recipes)

    return jsonify(recipes)

@app.route("/fetch-prices", methods=["POST"])
def fetch_prices():
    data = request.json
    ingredients = data.get("ingredients", [])
    store = data.get("store", "kroger").lower()
    prices = fetch_ingredient_prices(ingredients, store)
    return jsonify(prices)

@app.route("/add-to-cart", methods=["POST"])
def add_to_cart_route():
    user_token = session.get("kroger_user_token")
    if not user_token:
        print("No token found in session")  # Debugging
        return jsonify({"success": False, "error": "User not logged in to Kroger"}), 401

    data = request.json
    ingredients = data.get("items", [])
    if not ingredients:
        return jsonify({"success": False, "error": "No items provided"}), 400

    # Create a Kroger API instance for product lookup
    from store_handler import KrogerAPI
    client_id = "nutrifai-243261243034242e644175722e4a4c397a4e507a454732506e594e366576617532756c356b4741754c48746c31634a59564b784d4f2e364e7743462e3423701595089688646"
    client_secret = "f8IG7k0gYTJZNfHM9a22vaP0_ytGIYng2Acr9mIu"
    kroger_api = KrogerAPI(client_id, client_secret)
    
    # Get access token for product search
    search_token = kroger_api.request_token() # kroger_api.request_token()
    if not search_token:
        return jsonify({"success": False, "error": "Failed to authenticate for product search"}), 500
    
    # Search for products to get UPCs
    stores = kroger_api.get_kroger_stores(zip_code="97401", limit=1)
    if not stores:
        return jsonify({"success": False, "error": "No Kroger stores found"}), 500
    
    store_id = stores[0]["id"]
    ingredients_str = ",".join(ingredients)
    products = kroger_api.search_products(ingredients_str, location_id=store_id)
    
    # Add items to cart using UPCs
    success_list = []
    for ingredient, details in products.items():
        upc = details.get("UPC")
        if upc:
            success = add_item_to_cart(user_token, upc, quantity=1, modality="PICKUP")
            success_list.append(success)
        else:
            print(f"No UPC found for {ingredient}")
            success_list.append(False)

    if all(success_list) and success_list:
        return jsonify({"success": True, "message": f"Added {len(success_list)} items to Kroger cart"})
    else:
        return jsonify({"success": False, "error": "One or more items failed to add."})

@app.route("/login")
def login():
    """
    Redirects the user to Kroger's OAuth2 authorization endpoint
    requesting the cart.basic:write scope (so we can modify the cart).
    """
    scope = "cart.basic:write"
    authorize_url = (
        f"{AUTH_URL}?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={scope}"
    )
    return redirect(authorize_url)

@app.route("/callback")
def callback():
    """
    Kroger redirects here with ?code=XXXX after user logs in.
    We exchange that code for a user-level token, then store it in session.
    """
    auth_code = request.args.get("code", None)
    if not auth_code:
        return "No code provided by Kroger."

    user_token = exchange_code_for_token(auth_code)
    if not user_token:
        return "Failed to get user token from Kroger."

    # Store token in session
    session["kroger_user_token"] = user_token
    print("Token stored in session:", user_token)  # Debugging

    return """
    <h2>Successfully logged into Kroger!</h2>
    <p>You can now return to the React UI and click "Order with Kroger".</p>
    """

if __name__ == "__main__":
    app.run(debug=True, port=5000)