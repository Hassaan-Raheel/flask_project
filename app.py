from flask import Flask
from routes.routes_init import register_routes

app = Flask(__name__)

# Register the routes
register_routes(app)

@app.route('/', methods=['GET'])
def home():
    return "Welcome to the homepage! Go to /facebook to see Facebook data."

if __name__ == "__main__":
    app.run(debug=True)
