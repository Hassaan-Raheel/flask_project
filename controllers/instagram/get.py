import requests
import json
from flask import jsonify
from config import Config  # Make sure your Config file contains PAGE_ID and ACCESS_TOKEN

def get_instagram_data():
    try:
        # Step 1: Fetch the Instagram Business Account ID using the Facebook Graph API
        facebook_url = f"https://graph.facebook.com/{Config.PAGE_ID}?fields=instagram_business_account&access_token={Config.PAGE_ACCESS_TOKEN}"
        response = requests.get(facebook_url)

        if response.ok:
            data = response.json()
            instagram_business_account_id = data.get('instagram_business_account', {}).get('id')

            if not instagram_business_account_id:
                return jsonify({"error": "Instagram Business Account not found"}), 404

            # Step 2: Fetch Instagram media (posts) using the Instagram Business Account ID
            instagram_url = f"https://graph.instagram.com/{instagram_business_account_id}/media"
            params = {
                "fields": "id,caption,media_type,media_url,timestamp,permalink",
                "access_token": Config.PAGE_ACCESS_TOKEN
            }

            instagram_response = requests.get(instagram_url, params=params)

            if instagram_response.ok:
                instagram_data = instagram_response.json()
                posts = instagram_data.get('data', [])

                if not posts:
                    return jsonify({"error": "No posts found on the Instagram account"}), 404

                # Step 3: Prepare the post details for the response
                post_details = []
                for post in posts:
                    post_info = {
                        "post_id": post.get("id"),
                        "caption": post.get("caption", "No caption"),
                        "created_time": post.get("timestamp"),
                        "permalink_url": post.get("permalink"),
                        "media_url": post.get("media_url"),
                        "media_type": post.get("media_type")
                    }
                    post_details.append(post_info)

                return jsonify(post_details), 200
            else:
                return jsonify({"error": "Failed to fetch Instagram posts", "details": instagram_response.text}), instagram_response.status_code
        else:
            return jsonify({"error": "Failed to fetch Instagram Business Account", "details": response.text}), response.status_code

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

