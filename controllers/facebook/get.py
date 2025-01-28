import requests
from flask import jsonify
from config import Config

def get_facebook_data():
    # Facebook API URL and parameters
    url = f"https://graph.facebook.com/{Config.PAGE_ID}/published_posts"
    params = {
        "fields": "id,message,created_time,attachments{media,type},permalink_url",
        "access_token": Config.PAGE_ACCESS_TOKEN,
        "type": "video",  # Ensure this matches what you want
    }

    # Fetch data from the Facebook Graph API
    response = requests.get(url, params=params)

    # Check if the response was successful
    if response.ok:
        return jsonify(response.json())  # Return the fetched data as JSON
    else:
        return jsonify({"error": "Failed to fetch data", "details": response.text}), 400  # Return error with status
