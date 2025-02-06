import requests
import datetime
from flask import Blueprint, jsonify
from config import Config  # Ensure Config has PAGE_ID and PAGE_ACCESS_TOKEN

facebook_blueprint = Blueprint('facebook', __name__)

@facebook_blueprint.route('/facebook', methods=['GET'])

def get_facebook_data():
    """Fetches Facebook Page posts, reels (with center thumbnail), and cover image from the last 30 days."""
    
    try:
        # Step 1: Get the Page Access Token (using the App Access Token)
        token_url = f"https://graph.facebook.com/{Config.PAGE_ID}?fields=access_token&access_token={Config.PAGE_ACCESS_TOKEN}"
        token_response = requests.get(token_url)

        if token_response.ok:
            token_data = token_response.json()
            page_access_token = token_data.get("access_token")

            if not page_access_token:
                return jsonify({"error": "Failed to retrieve Page Access Token"}), 403

            # Step 2: Get Date Filters (Last 30 Days)
            today = datetime.datetime.utcnow()
            thirty_days_ago = today - datetime.timedelta(days=30)
            since = int(thirty_days_ago.timestamp())  
            until = int(today.timestamp())

            # Step 3: Fetch Facebook posts from the last 30 days
            posts_url = f"https://graph.facebook.com/{Config.PAGE_ID}/published_posts"
            posts_params = {
                "fields": "id,message,created_time,attachments{media,type},permalink_url",
                "since": since,
                "until": until,
                "access_token": page_access_token
            }

            posts_response = requests.get(posts_url, params=posts_params)
            posts_data = posts_response.json().get('data', []) if posts_response.ok else []
            
            for post in posts_data:
                if not post.get('message'):
                    continue  # Skip this post if there's no message
                
                image_url = None  # Default to None
                
                if 'attachments' in post and 'data' in post['attachments']:
                    attachment_data = post['attachments']['data'][0]  # Get first attachment
                    
                    if 'media' in attachment_data:
                        media = attachment_data['media']
                        
                        if 'image' in media and 'src' in media['image']:
                            image_url = media['image']['src']
                        elif 'source' in media:
                            image_url = media['source']

                post['image_url'] = image_url  # Add image URL to post data

            # Step 4: Fetch Facebook reels (Videos) from the last 30 days
            reels_url = f"https://graph.facebook.com/{Config.PAGE_ID}/videos"
            reels_params = {
                "fields": "id,description,created_time,permalink_url,thumbnails",
                "since": since,
                "until": until,
                "access_token": page_access_token
            }

            reels_response = requests.get(reels_url, params=reels_params)
            reels_data = reels_response.json().get('data', []) if reels_response.ok else []

            # Step 5: Fetch Facebook Cover Image
            cover_url = f"https://graph.facebook.com/{Config.PAGE_ID}?fields=cover&access_token={page_access_token}"
            cover_response = requests.get(cover_url)
            cover_image_url = cover_response.json().get("cover", {}).get("source", "No cover image found") if cover_response.ok else "No cover image found"

            # Step 6: Format response (Extract Center Thumbnail for Reels)
            formatted_reels = []
            for reel in reels_data:
                thumbnails = reel.get("thumbnails", {}).get("data", [])
                center_thumbnail = thumbnails[len(thumbnails) // 2]["uri"] if thumbnails else None

                formatted_reels.append({
                    "id": reel.get("id"),
                    "description": reel.get("description", "No description"),
                    "created_time": reel.get("created_time"),
                    "permalink_url": reel.get("permalink_url"),
                    "thumbnail": center_thumbnail  # Only center thumbnail
                })

            # Step 7: Structure final response data (counts at the top)
            response_data = {
                "total_posts": len(posts_data),  # ✅ Total number of posts
                "total_reels": len(reels_data),  # ✅ Total number of reels
                "cover_image": cover_image_url,
                "posts": [
                    {
                        "id": post.get("id"),
                        "message": post.get("message"),
                        "created_time": post.get("created_time"),
                        "permalink_url": post.get("permalink_url"),
                        "image_url": post.get("image_url", ""),
                        "image_tag": (
                            f'<img src="{post.get("image_url", "")}" alt="Post Image">' if post.get("image_url") else ""
                        )
                    }
                    for post in posts_data
                ],
                "reels": formatted_reels
            }

            return jsonify(response_data), 200

        else:
            return jsonify({"error": "Failed to retrieve Page Access Token", "details": token_response.text}), token_response.status_code

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


def get_facebook_ads_data():
    """Fetches Facebook Ads data, including insights like impressions, clicks, and spend."""
    try:
        # Step 1: Get Page Access Token
        token_url = f"https://graph.facebook.com/{Config.PAGE_ID}?fields=access_token&access_token={Config.PAGE_ACCESS_TOKEN}"
        token_response = requests.get(token_url)

        if token_response.ok:
            token_data = token_response.json()
            page_access_token = token_data.get("access_token")

            if not page_access_token:
                return jsonify({"error": "Failed to retrieve Page Access Token"}), 403

            # Step 2: Get Ad Account ID
            ad_account_url = f"https://graph.facebook.com/v13.0/{Config.PAGE_ID}/adaccounts"
            ad_account_response = requests.get(ad_account_url, params={"access_token": page_access_token})
            ad_account_data = ad_account_response.json().get('data', [])
            
            if not ad_account_data:
                return jsonify({"error": "No Ad Account associated with this page"}), 404
                
            ad_account_id = ad_account_data[0]['id']

            # Step 3: Fetch Ads Data
            ads_url = f"https://graph.facebook.com/v13.0/{ad_account_id}/ads"
            ads_params = {
                "fields": "id,name,adset_id,campaign_id,status,creative{image_url,body,title}",
                "access_token": page_access_token
            }
            ads_response = requests.get(ads_url, params=ads_params)

            if not ads_response.ok:
                return jsonify({"error": "Failed to fetch Ads", "details": ads_response.text}), ads_response.status_code

            ads_data = ads_response.json().get('data', [])

            if not ads_data:
                return jsonify({"error": "No ads found in the Ad Account"}), 404

            # Step 4: Fetch Insights Data (Optional)
            ads_with_insights = []
            for ad in ads_data:
                ad_id = ad.get("id")
                insights_url = f"https://graph.facebook.com/v13.0/{ad_id}/insights"
                insights_params = {
                    "fields": "impressions,clicks,spend",
                    "access_token": page_access_token
                }
                insights_response = requests.get(insights_url, params=insights_params)

                if insights_response.ok:
                    insights_data = insights_response.json().get('data', [])
                    ad["insights"] = insights_data
                else:
                    ad["insights"] = "No insights available"

                ads_with_insights.append(ad)

            return jsonify({"ads": ads_with_insights}), 200

        else:
            return jsonify({"error": "Failed to retrieve Page Access Token", "details": token_response.text}), token_response.status_code

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500
