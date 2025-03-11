import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_name='data.db'):
        """
        Initialize the Database connection and cursor.
        """
        self.connection = sqlite3.connect(db_name)
        self.crsr = self.connection.cursor()

        # Create a table with a column to store the recipe data as JSON
        create_table_sql = '''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_data TEXT NOT NULL
        );
        '''
        self.crsr.execute(create_table_sql)
        self.connection.commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Close the connection when done
        self.connection.close()

    def insert_recipe(self, recipe):
        """
        Insert a new recipe into the database.
        The recipe is a dictionary containing all necessary data.
        """
        # Serialize the recipe dictionary into a JSON string
        recipe_json = json.dumps(recipe)
        
        sql_command = '''
        INSERT INTO recipes (recipe_data) 
        VALUES (?);
        '''
        self.crsr.execute(sql_command, (recipe_json,))
        self.connection.commit()

    def get_recipe_by_id(self, recipe_id):
        """
        Get a recipe by its ID.
        """
        sql_command = 'SELECT * FROM recipes WHERE id = ?;'
        self.crsr.execute(sql_command, (recipe_id,))
        recipe = self.crsr.fetchone()  # Returns a tuple (id, recipe_data)
        
        if recipe:
            # Deserialize the recipe JSON string back into a dictionary
            recipe_data = json.loads(recipe[1])
            return recipe_data
        return None

    def get_all_recipes(self):
        """
        Get all recipes in the database.
        """
        print("entering get all")
        sql_command = 'SELECT * FROM recipes;'
        self.crsr.execute(sql_command)
        recipes = self.crsr.fetchall()  # Returns a list of tuples (id, recipe_data)
        print(recipes[0])
        
        # Deserialize the recipe data for each recipe
        return [json.loads(r[1]) for r in recipes]

    def delete_recipe(self, recipe_id):
        """
        Delete a recipe by its ID.
        """
        sql_command = 'DELETE FROM recipes WHERE id = ?;'
        self.crsr.execute(sql_command, (recipe_id,))
        self.connection.commit()
