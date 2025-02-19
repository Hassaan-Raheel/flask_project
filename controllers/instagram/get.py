import requests
import json
from flask import Blueprint, jsonify
from config import Config  # Ensure Config contains PAGE_ID and ACCESS_TOKEN

instagram_blueprint = Blueprint('instagram', __name__)

@instagram_blueprint.route('/instagram', methods=['GET'])
def get_instagram_data():
    try:
        # Step 1: Get Instagram Business Account ID
        facebook_url = f"https://graph.facebook.com/v19.0/{Config.PAGE_ID}?fields=instagram_business_account&access_token={Config.PAGE_ACCESS_TOKEN}"
        response = requests.get(facebook_url)

        if not response.ok:
            return jsonify({"error": "Failed to fetch Instagram Business Account", "details": response.text}), response.status_code

        data = response.json()
        instagram_business_account_id = data.get('instagram_business_account', {}).get('id')

        if not instagram_business_account_id:
            return jsonify({"error": "Instagram Business Account not found"}), 404

        # Step 2: Get Instagram Posts
        instagram_url = f"https://graph.facebook.com/v19.0/{instagram_business_account_id}/media"
        params = {
            "fields": "id,caption, shares_count,comments_count, like_count,media_type,media_url,thumbnail_url,timestamp,permalink,children{id,media_type,media_url,thumbnail_url}",
            "access_token": Config.PAGE_ACCESS_TOKEN
        }

        instagram_response = requests.get(instagram_url, params=params)

        if not instagram_response.ok:
            return jsonify({"error": "Failed to fetch Instagram posts", "details": instagram_response.text}), instagram_response.status_code

        instagram_data = instagram_response.json()
        posts = instagram_data.get('data', [])

        # Step 3: Process Instagram Posts
        post_details = []
        for post in posts:
            media_type = post.get("media_type")
            
            post_data = {
                "id": post.get("id"),
                "created_time": post.get("timestamp"),
                "media_type": media_type,
                "image_tag": f'<img src="{post.get("media_url")}" alt="Post Image">',
                "image_url": post.get("media_url"),
                "message": post.get("caption", "No caption"),
                "likes_count": post.get("like_count", 0),
                "comments_count": post.get("comments_count", 0),
                "shares_count": post.get("shares_count", 0),
                "permalink_url": post.get("permalink"),
                "thumbnail_url": post.get("thumbnail_url") if media_type == "VIDEO" else None
            }

            # Fetch engagement metrics for each post
            engagement_url = f"https://graph.facebook.com/v19.0/{post['id']}/insights"
            engagement_params = {
                "metric": "engagement,like_count,comments,reactions,shares",
                "access_token": Config.PAGE_ACCESS_TOKEN
            }

            engagement_response = requests.get(engagement_url, params=engagement_params)

            if engagement_response.ok:
                engagement_data = engagement_response.json().get("data", [])
                engagement_metrics = {item["name"]: item["values"][0]["value"] for item in engagement_data}

                post_data.update({
                    "likes_counts": engagement_metrics.get("likes", 0),
                    "comments_counts": engagement_metrics.get("comments", 0),
                    "shares_counts": engagement_metrics.get("shares", 0),
                    "reactions_count": engagement_metrics.get("reactions", 0),
                    "engagement": engagement_metrics.get("engagement", 0),
                })
            else:
                post_data.update({
                    "likes_counts": 0,
                    "comments_counts": 0,
                    "shares_counts": 0,
                    "reactions_count": 0,
                    "engagement": 0
                })

            # If it's a carousel, get the first image/video as the thumbnail
            if media_type == "CAROUSEL_ALBUM":
                children = post.get("children", {}).get("data", [])
                if children:
                    first_child = children[0]
                    post_data["thumbnail_url"] = first_child.get("thumbnail_url") or first_child.get("media_url")

            post_details.append(post_data)

        # Step 4: Get Instagram Insights (Followers, Reach)
        insights_url = f"https://graph.facebook.com/v19.0/{instagram_business_account_id}/insights"
        insights_params = {
            "metric": "follower_count,reach",
            "period": "day",
            "access_token": Config.PAGE_ACCESS_TOKEN
        }

        insights_response = requests.get(insights_url, params=insights_params)

        if not insights_response.ok:
            return jsonify({"error": "Failed to fetch Instagram insights", "details": insights_response.text}), insights_response.status_code

        insights_data = insights_response.json()
        insights = {item["name"]: item["values"][0]["value"] for item in insights_data.get("data", [])}

        # Step 5: Return Final Data
        return jsonify({
            "instagram_business_account_id": instagram_business_account_id,
            "insights": insights,
            "posts": post_details
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Request error", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500
