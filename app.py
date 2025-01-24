from flask import Flask

# Initialize the app
app = Flask(__name__)

# Import and register routes
from routes import register_routes
register_routes(app)

if __name__ == "__main__":
    app.run(debug=True)