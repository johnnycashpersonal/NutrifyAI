import pytest
import json
from datetime import datetime
from data import Database  # Assuming your Database class is in a file called database.py

@pytest.fixture
def db():
    """Fixture to create a fresh Database connection for each test."""
    with Database(":memory:") as db_instance:  # Use an in-memory database for testing
        yield db_instance


def test_insert_recipe(db):
    """Test that inserting a recipe works correctly."""
    recipe = {
        "name": "Pancakes",
        "ingredients": ["flour", "milk", "eggs"],
        "instructions": "Mix all ingredients and cook on a skillet.",
        "created_at": str(datetime.now())
    }
    
    db.insert_recipe(recipe)
    
    # Verify the recipe was inserted by fetching it
    fetched_recipe = db.get_recipe_by_id(1)
    
    assert fetched_recipe is not None
    assert fetched_recipe["name"] == "Pancakes"
    assert fetched_recipe["ingredients"] == ["flour", "milk", "eggs"]
    assert fetched_recipe["instructions"] == "Mix all ingredients and cook on a skillet."


def test_get_recipe_by_id(db):
    """Test retrieving a recipe by its ID."""
    recipe = {
        "name": "Spaghetti",
        "ingredients": ["pasta", "tomato sauce", "garlic"],
        "instructions": "Cook pasta and mix with sauce.",
        "created_at": str(datetime.now())
    }
    
    db.insert_recipe(recipe)
    
    # Fetch the recipe by ID
    fetched_recipe = db.get_recipe_by_id(1)
    
    assert fetched_recipe is not None
    assert fetched_recipe["name"] == "Spaghetti"


def test_get_all_recipes(db):
    """Test retrieving all recipes."""
    recipe1 = {
        "name": "Salad",
        "ingredients": ["lettuce", "tomato", "cucumber"],
        "instructions": "Chop and mix ingredients.",
        "created_at": str(datetime.now())
    }
    recipe2 = {
        "name": "Toast",
        "ingredients": ["bread", "butter"],
        "instructions": "Toast the bread and spread butter.",
        "created_at": str(datetime.now())
    }
    
    db.insert_recipe(recipe1)
    db.insert_recipe(recipe2)
    
    all_recipes = db.get_all_recipes()
    
    assert len(all_recipes) == 2
    assert all_recipes[0]["name"] == "Salad"
    assert all_recipes[1]["name"] == "Toast"


def test_delete_recipe(db):
    """Test deleting a recipe by ID."""
    recipe = {
        "name": "Omelette",
        "ingredients": ["eggs", "cheese", "salt"],
        "instructions": "Beat eggs, add cheese, and cook.",
        "created_at": str(datetime.now())
    }
    
    db.insert_recipe(recipe)
    
    # Ensure the recipe is in the database
    fetched_recipe = db.get_recipe_by_id(1)
    assert fetched_recipe is not None
    
    # Delete the recipe
    db.delete_recipe(1)
    
    # Ensure the recipe is deleted
    fetched_recipe = db.get_recipe_by_id(1)
    assert fetched_recipe is None


def test_insert_invalid_recipe(db):
    """Test inserting an invalid recipe."""
    invalid_recipe = {
        "name": "Invalid",
        "ingredients": ["ingredient1"],
        # Missing instructions, should raise an error or fail gracefully
    }
    
    # We should expect the insertion to succeed but return an incomplete recipe
    db.insert_recipe(invalid_recipe)
    
    fetched_recipe = db.get_recipe_by_id(1)
    
    assert fetched_recipe is not None
    assert fetched_recipe["name"] == "Invalid"
    assert "instructions" not in fetched_recipe  # Instructions key is missing


# Run tests with pytest
if __name__ == "__main__":
    pytest.main()
