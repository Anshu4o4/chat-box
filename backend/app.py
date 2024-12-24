import os
import random
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv  # Import dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Set up SQLAlchemy
Base = declarative_base()
DATABASE_URL = "sqlite:///ecommerce.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Define Product model
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=True)

# Create database tables
Base.metadata.create_all(engine)

# Store conversation history for each session (in-memory for simplicity)
conversation_history = []

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Sales Chatbot API!"})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('query', '').strip()

    # Predefined responses for greetings from environment variables
    if user_input.lower() in ["hi", "hii", "hiii", "hey", "helloo", "helo", "hello", "hallo"]:
        return jsonify({"answer": os.getenv("GREETING")})

    # Handle specific questions with predefined answers from environment variables
    if user_input.lower() in ["what is your name?", "what is ur name?", "whats ur name?", "whats your name?", "name", "what is your name", "your name"]:
        return jsonify({"answer": os.getenv("NAME_QUESTION")})

    if user_input.lower() in ["what games do you play?", "what games u play?", "wat games do u play?"]:
        return jsonify({"answer": os.getenv("GAME_QUESTION")})

    if user_input.lower() in ["do you play games?", "do u play games?", "do ya play games?"]:
        return jsonify({"answer": os.getenv("GAME_QUESTION")})

    # Add eCommerce clothing shop questions with variations
    if user_input.lower() in ["what is the return policy?", "wat is the return policy?"]:
        return jsonify({"answer": os.getenv("WHAT_IS_THE_RETURN_POLICY")})

    if user_input.lower() in ["how long does shipping take?", "how long shipping take?"]:
        return jsonify({"answer": os.getenv("HOW_LONG_DOES_SHIPPING_TAKE")})

    if user_input.lower() in ["how can i contact customer service?", "how to contact customer service?"]:
        return jsonify({"answer": os.getenv("HOW_CAN_I_CONTACT_CUSTOMER_SERVICE")})

    if user_input.lower() in ["tell me about t-shirts.", "tell me about tshirts.", "what is a t-shirt?"]:
        return jsonify({"answer": os.getenv("PRODUCT_INFO_TSHIRT")})

    if user_input.lower() in ["tell me about dresses.", "what kind of dresses do you sell?"]:
        return jsonify({"answer": os.getenv("PRODUCT_INFO_DRESS")})

    if user_input.lower() in ["what jeans do you have?", "tell me about your jeans."]:
        return jsonify({"answer": os.getenv("PRODUCT_INFO_JEANS")})

    if user_input.lower() in ["what jackets are available?", "tell me about your jackets."]:
        return jsonify({"answer": os.getenv("PRODUCT_INFO_JACKET")})

    # Add user input to conversation history
    conversation_history.append({"role": 'user', 'content': user_input})

    # Check for specific product queries using the database
    product_response = query_product_database(user_input)
    if product_response:
        conversation_history.append({"role": 'assistant', 'content': product_response})
        return jsonify({"answer": product_response})

    # Use OpenAI API for other queries
    response = get_openai_response(conversation_history)
    
    if response:
        conversation_history.append({"role": 'assistant', 'content': response})
        return jsonify({"answer": response})

    # Return a random fallback response if no answer is found
    fallback_response = random.choice([
        "I'm not quite sure how to answer that.",
        "Could you please rephrase your question?",
        "That's an interesting question! Let me think...",
        "I'm still learning, so I might not have the answer right now.",
    ])
    
    return jsonify({"answer": fallback_response})

def query_product_database(user_input):
    """Query the database for product information based on user input."""
    keywords = user_input.lower().split()
    
    products = session.query(Product).filter(Product.name.ilike(f"%{'%'.join(keywords)}%")).all()
    
    if products:
        responses = [f"{product.name}: {product.description} - Price: ${product.price}" for product in products]
        return "\n".join(responses)
    
    return None

def get_openai_response(conversation):
    """Fetches a response from the OpenAI GPT-3 model."""
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        return random.choice(["I can't access my information source right now."])

    headers = {
        'Authorization': f'Bearer {openai_api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": conversation,
        "max_tokens": 150  # Adjust max tokens based on your needs
    }
    
    try:
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
        response.raise_for_status()  
        response_json = response.json()
        
        if 'choices' in response_json and len(response_json['choices']) > 0:
            answer = response_json['choices'][0]['message']['content']
            return answer.strip()  
        
        return random.choice(["I'm not quite sure how to answer that."])
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from OpenAI: {e}")
        return random.choice(["I'm having trouble connecting to the information source right now."])

@app.route('/init', methods=['POST'])
def init_database():
    # Clear existing products in the database
    session.query(Product).delete()

    # Define mock products
    mock_products = [
        {"name": "Laptop", "category": "Electronics", "price": 999.99, "description": "A high-performance laptop."},
        {"name": "Book", "category": "Books", "price": 19.99, "description": "A fascinating novel."},
        {"name": "T-shirt", "category": "Clothing", "price": 9.99, "description": "A comfortable cotton T-shirt."},
        {"name": "Dress", "category": "Clothing", "price": 49.99, "description": "A stylish evening dress."},
        {"name": "Jeans", "category": "Clothing", "price": 39.99, "description": "Classic fit jeans."},
        {"name": "Jacket", "category": "Clothing", "price": 89.99, "description": "Warm winter jacket."},  # Ensure no non-breaking spaces here
        # Add more mock products as needed
    ]

    # Add new mock products to the database
    for product in mock_products:
        session.add(Product(**product))
        
    session.commit()  # Commit changes to the database

    return jsonify({"message": f"{len(mock_products)} products have been added to the database."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Ensure this line has no hidden characters
