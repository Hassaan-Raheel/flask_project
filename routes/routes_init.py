from flask import Blueprint
from controllers.facebook.get import get_facebook_data  # For Facebook
from controllers.instagram.get import get_instagram_data  # For Instagram

def register_routes(app):
    app.route('/facebook', methods=['GET'])(get_facebook_data)  # Facebook route
    app.route('/instagram', methods=['GET'])(get_instagram_data)  # Instagram route
