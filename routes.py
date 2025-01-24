import os
import requests
from flask import jsonify

def register_routes(app):
    @app.route('/facebook', methods=['GET'])
    def get_facebook_data():
        # Access token and page ID
        page_access_token = os.getenv("PAGE_ACCESS_TOKEN", "your_default_token")
        page_id = os.getenv("PAGE_ID", "your_default_page_id")

        # Fetch reels from Facebook Graph API
        url = f"https://graph.facebook.com/{page_id}/published_posts"
        params = {
            "fields": "id,message,created_time,attachments{media,type},permalink_url",
            "access_token": page_access_token,
            "type": "video",
        }
        response = requests.get(url, params=params)

        if response.ok:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to fetch data", "details": response.text}), response.status_code