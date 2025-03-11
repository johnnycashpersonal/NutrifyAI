import pytest
import requests
from unittest.mock import MagicMock
from your_kroger_file import KrogerAPI  # Replace 'your_kroger_file' with your actual filename

@pytest.fixture
def kroger_api():
    """Fixture to create a KrogerAPI instance with dummy credentials."""
    return KrogerAPI(client_id="test_client_id", client_secret="test_client_secret")

def test_request_token_success(kroger_api, monkeypatch):
    """Test that KrogerAPI successfully retrieves an access token."""
    
    def mock_post(*args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test_access_token"}
        return mock_response

    monkeypatch.setattr(requests, "post", mock_post)
    
    token = kroger_api.request_token()
    assert token == "test_access_token"
    assert kroger_api.access_token == "test_access_token"

def test_request_token_failure(kroger_api, monkeypatch):
    """Test handling of invalid credentials (400 error)."""

    def mock_post(*args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid credentials"
        return mock_response

    monkeypatch.setattr(requests, "post", mock_post)
    
    token = kroger_api.request_token()
    assert token is None

def test_get_kroger_stores(kroger_api, monkeypatch):
    """Test fetching stores by ZIP code."""

    def mock_get(*args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "locationId": "123",
                    "name": "Test Kroger Store",
                    "address": {
                        "addressLine1": "123 Main St",
                        "city": "Eugene",
                        "state": "OR",
                        "zipCode": "97401"
                    }
                }
            ]
        }
        return mock_response

    monkeypatch.setattr(requests, "get", mock_get)
    kroger_api.access_token = "test_access_token"

    stores = kroger_api.get_kroger_stores("97401")
    assert len(stores) == 1
    assert stores[0]["id"] == "123"
    assert stores[0]["name"] == "Test Kroger Store"

def test_search_products(kroger_api, monkeypatch):
    """Test searching for the cheapest product per search term."""

    def mock_get(*args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "upc": "0001111060903",
                    "items": [
                        {"price": {"regular": "2.99"}}
                    ]
                },
                {
                    "upc": "0001111060904",
                    "items": [
                        {"price": {"regular": "3.99"}}
                    ]
                }
            ]
        }
        return mock_response

    monkeypatch.setattr(requests, "get", mock_get)
    kroger_api.access_token = "test_access_token"

    products = kroger_api.search_products("milk")
    assert "milk" in products
    assert products["milk"]["UPC"] == "0001111060903"
    assert products["milk"]["Price"] == 2.99

def test_search_multiple_products(kroger_api, monkeypatch):
    """Test searching for multiple products and getting the cheapest one per item."""

    def mock_get(*args, **kwargs):
        # Simulate different responses for each item
        item = kwargs["params"]["filter.term"]
        mock_response = MagicMock()
        mock_response.status_code = 200
        if item == "milk":
            mock_response.json.return_value = {
                "data": [{"upc": "0001111060903", "items": [{"price": {"regular": "2.99"}}]}]
            }
        elif item == "egg":
            mock_response.json.return_value = {
                "data": [{"upc": "0002222060903", "items": [{"price": {"regular": "1.99"}}]}]
            }
        return mock_response

    monkeypatch.setattr(requests, "get", mock_get)
    kroger_api.access_token = "test_access_token"

    products = kroger_api.search_products("milk,egg")
    assert products["milk"]["UPC"] == "0001111060903"
    assert products["milk"]["Price"] == 2.99
    assert products["egg"]["UPC"] == "0002222060903"
    assert products["egg"]["Price"] == 1.99
