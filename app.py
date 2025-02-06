from flask import Flask
from flask_cors import CORS
from routes.routes_init import register_routes  # Import register_routes function

app = Flask(__name__)

CORS(app)

# Register the routes via blueprints
register_routes(app)

@app.route('/', methods=['GET'])
def home():
    return "Welcome to the homepage! Go to /facebook to see Facebook data."

if __name__ == "__main__":
    app.run(debug=True)
