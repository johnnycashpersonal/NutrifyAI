import React, { useState, useEffect } from 'react';
import {
  MessageCircle,
  Compass,
  ChevronDown,
  Info,
  User,
  ShoppingCart,
  ArrowLeft,
  Search,
  Save,
  X,
  Check,
  Send
} from 'lucide-react';
import './NutrifyAI.css';

const NutrifyAI = () => {
  const [inputValue, setInputValue] = useState('');
  const [currentView, setCurrentView] = useState('input'); // 'input', 'details', or 'pastRecipes'
  const [currentRecipe, setCurrentRecipe] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chatInput, setChatInput] = useState('');
  const [modificationLoading, setModificationLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [cartStatus, setCartStatus] = useState(null); // State for cart overlay status
  const [recipeSaving, setRecipeSaving] = useState(false); // State to track save recipe operation
  const [pastRecipes, setPastRecipes] = useState([]); // NEW state for past recipes
  const [pastRecipesLoading, setPastRecipesLoading] = useState(false); // NEW state for loading indicator
  
  // Sample recipe data as fallback
  const sampleRecipe = {
    name: "Mediterranean Quinoa Bowl",
    ingredients: [
      { name: "Quinoa", amount: "1 cup", inPantry: true },
      { name: "Cherry Tomatoes", amount: "1 cup, halved", inPantry: false },
      { name: "Cucumber", amount: "1/2, diced", inPantry: true },
      { name: "Kalamata Olives", amount: "1/4 cup, sliced", inPantry: false },
      { name: "Feta Cheese", amount: "1/2 cup, crumbled", inPantry: false },
      { name: "Olive Oil", amount: "2 tbsp", inPantry: true },
      { name: "Lemon Juice", amount: "1 tbsp", inPantry: true },
      { name: "Fresh Mint", amount: "2 tbsp, chopped", inPantry: false }
    ],
    instructions: [
      "Cook quinoa according to package directions and let cool.",
      "Combine all ingredients in a large bowl.",
      "Drizzle with olive oil and lemon juice.",
      "Toss gently to combine and serve."
    ]
  };
  
  // The base URL for the API
  const API_URL = 'http://127.0.0.1:5000';
  // NEW Function to fetch past recipes
  const fetchPastRecipes = async () => {
    setPastRecipesLoading(true);
    try {
      const response = await fetch(`${API_URL}/get-past`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch past recipes');
      }
      
      const data = await response.json();
      
      // Format the recipes properly
      const formattedRecipes = data.map(item => ({
        ...item.recipe,
        // Ensure ingredients have the confirmed property
        ingredients: item.recipe.ingredients.map(ing => ({
          ...ing,
          confirmed: false
        }))
      }));
      
      setPastRecipes(formattedRecipes);
    } catch (error) {
      console.error('Error fetching past recipes:', error);
      // Use empty array if error occurs
      setPastRecipes([]);
    } finally {
      setPastRecipesLoading(false);
    }
  };
  
  // Fetch past recipes when visiting the Past Recipes view
  useEffect(() => {
    if (currentView === 'pastRecipes') {
      fetchPastRecipes();
    }
  }, [currentView]);
  
  // Function to fetch recipe from our Python backend
  const fetchRecipeFromAPI = async (description) => {
    try {
      const response = await fetch(`${API_URL}/generate-recipe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ description }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch recipe');
      }
      
      const data = await response.json();
      
      // The API now returns both raw text and structured recipe
      return data.structured_recipe;
    } catch (error) {
      console.error('Error fetching recipe:', error);
      throw error;
    }
  };
  
  // Function to modify existing recipe through the API
  const modifyRecipeFromAPI = async (originalRecipe, modifications) => {
    try {
      const response = await fetch(`${API_URL}/modify-recipe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          original_recipe: originalRecipe,
          modifications: modifications
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to modify recipe');
      }
      
      const data = await response.json();
      return data.modified_recipe;
    } catch (error) {
      console.error('Error modifying recipe:', error);
      throw error;
    }
  };
  
  // Function to fetch prices for ingredients
  const fetchIngredientPrices = async (ingredients, store = 'kroger') => {
    try {
      const response = await fetch(`${API_URL}/fetch-prices`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ingredients: ingredients.map(ing => ing.name),
          store
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch prices');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching prices:', error);
      return null;
    }
  };
  
  // Function to add items to cart
  const addItemsToCart = async (items, store = 'kroger') => {
    try {
      const response = await fetch(`${API_URL}/add-to-cart`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ items, store }),
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('click the login with kroger button to authenticate');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error adding to cart:', error);
      return { success: false, error: error.message };
    }
  };
  
  // Function to save recipe to database
  const saveRecipeToDatabase = async (recipe) => {
    try {
      const response = await fetch(`${API_URL}/save-recipe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ recipe }),
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to save recipe');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error saving recipe:', error);
      return { success: false, error: error.message };
    }
  };
  
  // Handle recipe submission with API call
  const handleSubmitRecipe = async () => {
    if (inputValue.trim() === '') return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Call our Python backend API
      const recipe = await fetchRecipeFromAPI(inputValue);
      
      // Add pantry status to ingredients (randomly for demo)
      const recipeWithPantry = {
        ...recipe,
        ingredients: recipe.ingredients.map(ingredient => ({
          ...ingredient,
          confirmed: true,
        })),
      };
      
      setCurrentRecipe(recipeWithPantry);
      setCurrentView('details');
    } catch (error) {
      console.error("Error getting recipe:", error);
      setError("Failed to fetch recipe. Using sample recipe instead.");
      
      // Fallback to sample recipe
      setCurrentRecipe({
        ...sampleRecipe,
        ingredients: sampleRecipe.ingredients.map(ingredient => ({
          ...ingredient,
          confirmed: false
        }))
      });
      setCurrentView('details');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle sending a recipe modification request
  const handleRecipeModification = async () => {
    if (chatInput.trim() === '') return;
    
    setModificationLoading(true);
    
    // Add user message to chat history
    const newMessage = { 
      text: chatInput,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    
    setChatHistory(prevHistory => [...prevHistory, newMessage]);
    setChatInput('');
    
    try {
      // Call the API to modify the recipe
      const modifiedRecipe = await modifyRecipeFromAPI(currentRecipe, chatInput);
      
      // Keep pantry status and confirmation for ingredients that exist in both recipes
      const updatedRecipe = {
        ...modifiedRecipe,
        ingredients: modifiedRecipe.ingredients.map(newIngredient => {
          // Try to find this ingredient in the current recipe
          const existingIngredient = currentRecipe.ingredients.find(
            ing => ing.name.toLowerCase() === newIngredient.name.toLowerCase()
          );
          
          return {
            ...newIngredient,
            inPantry: existingIngredient ? existingIngredient.inPantry : Math.random() > 0.6,
            confirmed: existingIngredient ? existingIngredient.confirmed : false
          };
        })
      };
      
      // Add system response to chat history
      setChatHistory(prevHistory => [
        ...prevHistory,
        { 
          text: `Recipe updated: "${modifiedRecipe.name}"`,
          sender: 'system',
          timestamp: new Date().toISOString()
        }
      ]);
      
      setCurrentRecipe(updatedRecipe);
    } catch (error) {
      console.error("Error modifying recipe:", error);
      
      // Add error message to chat history
      setChatHistory(prevHistory => [
        ...prevHistory,
        { 
          text: "Sorry, I couldn't modify the recipe. Please try a different request.",
          sender: 'system',
          timestamp: new Date().toISOString(),
          isError: true
        }
      ]);
    } finally {
      setModificationLoading(false);
    }
  };
  
  // Handle removing an ingredient (unused in final UI, but kept here if needed)
  const handleRemoveIngredient = (indexToRemove) => {
    const updatedRecipe = { ...currentRecipe };
    updatedRecipe.ingredients = updatedRecipe.ingredients.filter((_, index) => index !== indexToRemove);
    setCurrentRecipe(updatedRecipe);
  };
  
  // Handle confirming an ingredient
  const handleConfirmIngredient = (index) => {
    const updatedRecipe = { ...currentRecipe };
    updatedRecipe.ingredients[index].confirmed = !updatedRecipe.ingredients[index].confirmed;
    setCurrentRecipe(updatedRecipe);
  };
  
  // Handle ordering with Kroger
  const handleOrderWithKroger = async () => {
    const confirmedIngredients = currentRecipe.ingredients
      .filter(ing => ing.confirmed && !ing.inPantry)
      .map(ing => ing.name);

    if (confirmedIngredients.length === 0) {
      alert("Please confirm at least one ingredient to order");
      return;
    }

    setLoading(true);
    setCartStatus('adding'); // Show "adding" overlay

    try {
      const result = await addItemsToCart(confirmedIngredients, 'kroger');

      if (result.success) {
        setCartStatus('success'); // Show success overlay & "Go to Cart" button
      } else {
        setCartStatus('error');   // Show error overlay
      }
    } catch (error) {
      setCartStatus('error');     // Show error overlay
    } finally {
      setLoading(false);
    }
  };

  // Handler for saving recipe
  const handleSaveRecipe = async () => {
    if (!currentRecipe) return;
    
    // Set saving state - used internally, not displayed in UI
    setRecipeSaving(true);
    
    try {
      // Prepare recipe data for saving
      const recipeToSave = {
        name: currentRecipe.name,
        ingredients: currentRecipe.ingredients.map(ing => ({
          name: ing.name,
          amount: ing.amount,
          inPantry: ing.inPantry
        })),
        instructions: currentRecipe.instructions,
        dateCreated: new Date().toISOString()
      };
      
      // Call API to save recipe
      const result = await saveRecipeToDatabase(recipeToSave);
      
      console.log("Recipe saved:", result);
      
    } catch (error) {
      console.error("Error saving recipe:", error);
    } finally {
      setRecipeSaving(false);
    }
  };

  // Helper function to format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  // Helper function to create a short description from the recipe
  const createRecipeDescription = (recipe) => {
    const ingredients = recipe.ingredients.slice(0, 3).map(ing => ing.name).join(', ');
    return `A recipe with ${ingredients}${recipe.ingredients.length > 3 ? ', and more' : ''}.`;
  };

  return (
    <div className="nutrify-container">
      {/* ---------- SIDEBAR ---------- */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="logo-container">
            <MessageCircle size={16} />
          </div>
          <span className="logo-text">Nutrify AI</span>
          <ChevronDown className="dropdown-icon" size={16} />
        </div>
        
        {/* Navigation menu */}
        <div className="nav-menu">
          <button 
            className="nav-item"
            onClick={() => setCurrentView('pastRecipes')}
          >
            <Compass size={16} />
            <span>Recipe History</span>
          </button>
        </div>

        {/* Login button moved up, with proper styling */}
        <div className="nav-item-container" style={{ padding: "15px 20px", marginBottom: "20px" }}>
          <button
            className="upgrade-button"
            onClick={() => window.open("http://127.0.0.1:5000/login", "_blank")}
          >
            <Info size={16} />
            <span>Login with Kroger</span>
          </button>
        </div>
      </div>

      {/* ---------- MAIN CONTENT ---------- */}
      <div className="main-content">
        {/* Profile icon in top-right */}
        <div className="profile-container">
          <button
            className="profile-button"
            onClick={() => setProfileOpen(!profileOpen)}
          >
            <User size={20} />
          </button>
          
          {/* Profile dropdown */}
          {profileOpen && (
            <div className="profile-dropdown">
              <div className="profile-header">
                <span>John Doe</span>
                <span className="profile-email">john.doe@example.com</span>
              </div>
              <div className="profile-section">
                <button className="profile-option">Profile Settings</button>
                <button className="profile-option">Order History</button>
                <button className="profile-option">Saved Recipes</button>
                <button className="profile-option">My Pantry</button>
                <button className="profile-option">Sign Out</button>
              </div>
            </div>
          )}
        </div>
        
        {/* ---------- INPUT VIEW ---------- */}
        {currentView === 'input' && (
          <div className="chat-area">
            <h1 className="main-heading">What would you like to cook today?</h1>
            <div className="center-query-container">
              <div className="center-input-wrapper">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Enter a recipe or dish you want to make..."
                  className="center-text-input"
                  disabled={loading}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !loading) handleSubmitRecipe();
                  }}
                />
                <div className="center-input-buttons">
                  <button
                    className="icon-button"
                    onClick={handleSubmitRecipe}
                    disabled={loading}
                  >
                    {loading ? (
                      <div className="loading-spinner"></div>
                    ) : (
                      <Search size={18} />
                    )}
                  </button>
                  {/* Removed microphone button */}
                </div>
              </div>
              
              {/* Loading message */}
              {loading && (
                <div className="loading-message">
                  Generating your recipe with AI... This may take a moment.
                </div>
              )}
              
              {/* Error message */}
              {error && (
                <div className="error-message">
                  {error}
                </div>
              )}
              
              {/* Disclaimer */}
              <div className="disclaimer-container">
                <div className="disclaimer">
                  Nutrify AI helps you find recipes and purchase ingredients from grocery delivery services.
                  Always check for allergens and nutritional information.
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* ---------- DETAILS VIEW ---------- */}
        {currentView === 'details' && currentRecipe && (
          <div className="recipe-details">
            <button
              className="back-button"
              onClick={() => setCurrentView('input')}
            >
              <ArrowLeft size={16} />
              <span>Back to Search</span>
            </button>
            
            <h1 className="recipe-title">{currentRecipe.name}</h1>
            
            <div className="recipe-content">
              <div className="ingredients-section">
                <h2>Ingredients</h2>
                <div className="ingredients-list">
                  {currentRecipe.ingredients.map((ingredient, index) => (
                    <div
                      key={index}
                      className={`ingredient-item ${ingredient.confirmed ? 'confirmed' : 'unconfirmed'}`}
                    >
                      <span className="ingredient-name">{ingredient.name}</span>
                      <span className="ingredient-amount">{ingredient.amount}</span>
                      <div className="ingredient-actions">
                        <button
                          className={`confirm-button ${ingredient.confirmed ? 'confirmed' : ''}`}
                          onClick={() => handleConfirmIngredient(index)}
                          title={ingredient.confirmed ? "Unconfirm" : "Confirm"}
                        >
                          <Check size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="missing-ingredients">
                  <h3>Ingredients to Purchase</h3>
                  <p>
                    {currentRecipe.ingredients.filter(i => !i.inPantry).length} items needed
                    ({currentRecipe.ingredients.filter(i => !i.inPantry && i.confirmed).length} confirmed)
                  </p>
                  
                  <div className="grocery-options">
                    <button
                      className="grocery-button kroger"
                      onClick={handleOrderWithKroger}
                      disabled={
                        loading ||
                        currentRecipe.ingredients.filter(i => !i.inPantry && i.confirmed).length === 0
                      }
                    >
                      <ShoppingCart size={16} />
                      <span>Order with Kroger</span>
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="instructions-section">
                <h2>Instructions</h2>
                <ol className="instructions-list">
                  {currentRecipe.instructions.map((step, index) => (
                    <li key={index} className="instruction-step">
                      {step}
                    </li>
                  ))}
                </ol>
                
                <button 
                  className="save-recipe-button"
                  onClick={handleSaveRecipe}
                  disabled={recipeSaving}
                >
                  <Save size={16} />
                  <span>Save to My Recipes</span>
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* ---------- PAST RECIPES VIEW ---------- */}
        {currentView === 'pastRecipes' && (
          <div className="past-recipes">
            <button
              className="back-button"
              onClick={() => setCurrentView('input')}
            >
              <ArrowLeft size={16} />
              <span>Back to Search</span>
            </button>
            
            <h1 className="past-recipes-title">Your Recipe History</h1>
            
            {pastRecipesLoading ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Loading your recipes...</p>
              </div>
            ) : pastRecipes.length === 0 ? (
              <div className="no-recipes-message">
                <p>You don't have any saved recipes yet.</p>
                <button 
                  className="primary-button"
                  onClick={() => setCurrentView('input')}
                >
                  Create Your First Recipe
                </button>
              </div>
            ) : (
              <div className="recipe-history-grid">
                {pastRecipes.map((recipe, index) => (
                  <div key={index} className="recipe-card">
                    <div className="recipe-card-header">
                      <h3>{recipe.name}</h3>
                      <span className="recipe-date">
                        {recipe.dateCreated ? formatDate(recipe.dateCreated) : 'No date'}
                      </span>
                    </div>
                    <p className="recipe-description">
                      {createRecipeDescription(recipe)}
                    </p>
                    <div className="recipe-card-actions">
                      <button
                        className="card-action-button"
                        onClick={() => {
                          // Make sure all ingredients have the confirmed property
                          const preparedRecipe = {
                            ...recipe,
                            ingredients: recipe.ingredients.map(ingredient => ({
                              ...ingredient,
                              confirmed: false
                            }))
                          };
                          setCurrentRecipe(preparedRecipe);
                          setCurrentView('details');
                        }}
                      >
                        View Recipe
                      </button>
                      <button
                        className="card-action-button"
                        onClick={() => {
                          // Make sure all ingredients have the confirmed property, and
                          // auto-confirm items not in pantry
                          const preparedRecipe = {
                            ...recipe,
                            ingredients: recipe.ingredients.map(ingredient => ({
                              ...ingredient,
                              confirmed: !ingredient.inPantry
                            }))
                          };
                          setCurrentRecipe(preparedRecipe);
                          setCurrentView('details');
                        }}
                      >
                        Reorder
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* ---------- CART STATUS OVERLAYS ---------- */}
      {cartStatus && (
        <div className="cart-status-overlay">
          <div className={`cart-status-box ${cartStatus}`}>
            {cartStatus === 'adding' && (
              <>
                <div className="loading-animation">
                  <div className="cart-loader"></div>
                </div>
                <h3>Adding Items to Kroger</h3>
                <p>Please wait while we add your ingredients to your Kroger cart.</p>
                <div className="progress-bar">
                  <div className="progress-fill"></div>
                </div>
                <button 
                  className="secondary-button" 
                  onClick={() => setCartStatus(null)}
                >
                  Cancel
                </button>
              </>
            )}

            {cartStatus === 'success' && (
              <>
                <div className="status-icon success">
                  <Check size={32} />
                </div>
                <h3>Success!</h3>
                <p>All items have been added to your Kroger cart</p>
                <div className="action-buttons">
                  <button
                    className="primary-button"
                    onClick={() => window.open('https://www.kroger.com/cart', '_blank')}
                  >
                    <ShoppingCart size={16} />
                    Go to Kroger Cart
                  </button>
                  <button 
                    className="secondary-button" 
                    onClick={() => setCartStatus(null)}
                  >
                    Continue Making Recipes
                  </button>
                </div>
              </>
            )}

            {cartStatus === 'error' && (
              <>
                <div className="status-icon error">
                  <X size={32} />
                </div>
                <h3>Connection Error</h3>
                <p>We couldn't add items to your Kroger cart</p>
                <p className="error-detail">Please make sure you've logged in with your Kroger account</p>
                <div className="action-buttons">
                  <button
                    className="primary-button"
                    onClick={() => window.open("http://127.0.0.1:5000/login", "_blank")}
                  >
                    Login with Kroger
                  </button>
                  <button 
                    className="secondary-button" 
                    onClick={() => setCartStatus(null)}
                  >
                    Try Again Later
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NutrifyAI;
