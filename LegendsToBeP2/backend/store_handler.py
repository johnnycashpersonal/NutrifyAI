import requests
import base64

# Define what gets exported when someone imports from this file
__all__ = ['fetch_ingredient_prices', 'KrogerAPI']

class KrogerAPI:
    def __init__(self, client_id, client_secret):
        """
        Initializes the KrogerAPI class with client credentials.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://api.kroger.com/v1"

    def get_encoded_credentials(self):
        """
        This step is required for OAuth2 authentication.
        """
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return encoded_credentials

    def request_token(self):
        """
        Requests an OAuth2 access token using client credentials.
        """
        url = f"{self.base_url}/connect/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self.get_encoded_credentials()}"
        }
        data = {
            "grant_type": "client_credentials",
            "scope": "product.compact profile.compact"
        }

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            self.access_token = response.json().get("access_token", "")
            return self.access_token
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None

    def get_kroger_stores(self, zip_code, limit=10):
        """
        Fetches Kroger stores near a given ZIP code.
        
        :param zip_code: ZIP code to search stores near
        :param limit: Number of stores to fetch (default: 10)
        :return: List of store details
        """
        if not self.access_token:
            print("Error: No access token available. Request one first.")
            return []

        url = f"{self.base_url}/locations"
        params = {
            "filter.zipCode.near": zip_code,
            "filter.limit": limit
        }
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            stores = [
                {
                    "id": store.get("locationId"),
                    "name": store.get("name", "Unknown Store"),
                    "address": store["address"].get("addressLine1", "Unknown Address"),
                    "city": store["address"].get("city", ""),
                    "state": store["address"].get("state", ""),
                    "zip": store["address"].get("zipCode", ""),
                }
                for store in data.get("data", [])
            ]
            return stores
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return []

    def search_products(self, search_terms, location_id=None, limit=10, start=0):
        """
        Searches for multiple products in the Kroger catalog with pagination
        and returns the UPC and price of the lowest-cost item for each search term.
        
        :param search_terms: A single item or comma-separated items (e.g., "milk" or "bread, eggs, cheese")
        :param location_id: Optional location ID to get store-specific prices, inventory, and aisle info
        :param limit: Number of results per item to fetch (default: 10)
        :param start: Number of results to skip (pagination support)
        :return: Dictionary mapping each search term to {'UPC': lowest-cost item's UPC, 'Price': price}.
        """
        if not self.access_token:
            print("Error: No access token available. Request one first.")
            return {}

        url = f"{self.base_url}/products"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        search_items = [item.strip() for item in search_terms.split(",")]
        cheapest_items = {}

        for item in search_items:
            lowest_price = float('inf')
            lowest_price_upc = None

            params = {
                "filter.term": item,
                "filter.limit": limit,
                "filter.start": start
            }

            if location_id:
                params["filter.locationId"] = location_id

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                for product in data.get("data", []):
                    price = product.get("items", [{}])[0].get("price", {}).get("regular", None)
                    upc = product.get("upc", None)

                    if price is not None and upc is not None:
                        try:
                            price = float(price)
                            if price < lowest_price:
                                lowest_price = price
                                lowest_price_upc = upc
                        except ValueError:
                            continue  # Skip invalid price values

            else:
                print(f"Error fetching {item}: {response.status_code}, {response.text}")

            # Store the cheapest item's UPC and price for this search term
            cheapest_items[item] = {
                "UPC": lowest_price_upc,
                "Price": lowest_price if lowest_price != float('inf') else None
            }

        return cheapest_items
#returns stuff in this format
#{'steak': {'UPC': '0001111036547', 'Price': 5.99}, 'egg': {'UPC': '0001111090406', 'Price': 2.99}, 'milk': {'UPC': '0001111050578', 'Price': 2.99}, 'bread': {'UPC': '0001111008415', 'Price': 3.79}}


def fetch_ingredient_prices(ingredients, store="kroger"):
    """
    Fetch prices for a list of ingredient strings using the KrogerAPI.
    Returns a list of dicts, one per ingredient, with 'ingredient', 'productName', and 'price'.
    """
    from dotenv import load_dotenv
    load_dotenv()  # Ensure KROGER_CLIENT_ID, KROGER_CLIENT_SECRET are in .env

    client_id = "nutrify-2432612430342445574c6e2f4174746941377459497376313952524f754958446f585241614a675677526d5646354f547a71502f4631365747572e4b1774410088019709705"
    client_secret = "QkJnE0XrFDHIl1Y2BH9H1lFp96BYHU24fFfA2ZTL"

    if not client_id or not client_secret:
        return {"error": "Kroger credentials not found in environment variables."}

    kroger_api = KrogerAPI(client_id, client_secret)
    token = kroger_api.request_token()
    if not token:
        return {"error": "Failed to obtain Kroger API token."}

    # For now, pick the first store near a default ZIP code, e.g. 97401
    stores = kroger_api.get_kroger_stores(zip_code="97401", limit=1)
    if not stores:
        return {"error": "No Kroger stores found near ZIP code 97401."}
    store_id = stores[0]["id"]

    # Search for each ingredient and gather the first matching product + price
    results = []
    for ing in ingredients:
        products = kroger_api.search_products(
            search_terms=ing,
            location_id=store_id,
            limit=1
        )
        if products:
            product = products[0]
            results.append({
                "ingredient": ing,
                "productName": product["name"],
                "price": product["price"],
            })
        else:
            # If no product found, return a None entry
            results.append({
                "ingredient": ing,
                "productName": None,
                "price": None,
            })
    return results

# I didn't make this but I didn't want to delete it either

# Example usage:
if __name__ == "__main__":
    CLIENT_ID = "nutrify-2432612430342445574c6e2f4174746941377459497376313952524f754958446f585241614a675677526d5646354f547a71502f4631365747572e4b1774410088019709705"
    CLIENT_SECRET = "QkJnE0XrFDHIl1Y2BH9H1lFp96BYHU24fFfA2ZTL"
    
    kroger_api = KrogerAPI(CLIENT_ID, CLIENT_SECRET)
    access_token = kroger_api.request_token()

    if access_token:
        # Search for a nearby store first
        stores = kroger_api.get_kroger_stores(zip_code="97401", limit=1)
        store_id = stores[0]["id"] if stores else None

        # Example: search for products
        items_to_search = "steak,egg,milk,bread"
        products = kroger_api.search_products(items_to_search, location_id=store_id, start=0)
        print("Cheapest products found:")
        for item, details in products.items():
            print(f"{item}: UPC {details['UPC']}, Price ${details['Price']}")


