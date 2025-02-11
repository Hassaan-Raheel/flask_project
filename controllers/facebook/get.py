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

            # Step 3: Fetch Facebook posts with engagement data
            posts_url = f"https://graph.facebook.com/{Config.PAGE_ID}/published_posts"
            posts_params = {
                "fields": "id,message,created_time,attachments{media,type},permalink_url,"
                          "likes.summary(true),reactions.summary(true),comments.summary(true),shares",
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

                # Add engagement data
                post['likes_count'] = post.get('likes', {}).get('summary', {}).get('total_count', 0)
                post['reactions_count'] = post.get('reactions', {}).get('summary', {}).get('total_count', 0)
                post['comments_count'] = post.get('comments', {}).get('summary', {}).get('total_count', 0)
                post['shares_count'] = post.get('shares', {}).get('count', 0)

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
            
            # Step 5: Fetch Facebook Cover Image and Additional Details (From the first code)
            cover_url = f"https://graph.facebook.com/{Config.PAGE_ID}?fields=cover&access_token={page_access_token}"
            cover_response = requests.get(cover_url)

            cover_image_url = "No cover image found"
            cover_id = "No cover ID found"
            cover_created_time = "No cover creation date found"
            cover_caption = "No cover caption found"
            cover_engagement = {
                "likes_count": 0,
                "comments_count": 0,
                "shares_count": 0,
                "reactions_count": 0
            }

            if cover_response.ok:
                cover_data = cover_response.json().get("cover", {})
                if cover_data:
                    cover_image_url = cover_data.get("source", cover_image_url)
                    cover_id = cover_data.get("id", cover_id)
                    cover_created_time = cover_data.get("created_time", cover_created_time)
                    cover_caption = cover_data.get("caption", cover_caption)

                    # Fetch cover engagement metrics if available
                    cover_engagement_url = f"https://graph.facebook.com/{cover_id}?fields=likes,comments,reactions,shares&access_token={page_access_token}"
                    cover_engagement_response = requests.get(cover_engagement_url)

                    if cover_engagement_response.ok:
                        engagement_data = cover_engagement_response.json()
                        cover_engagement = {
                            "likes_count": engagement_data.get("likes", {}).get("summary", {}).get("total_count", 0),
                            "comments_count": engagement_data.get("comments", {}).get("summary", {}).get("total_count", 0),
                            "shares_count": engagement_data.get("shares", {}).get("count", 0),
                            "reactions_count": engagement_data.get("reactions", {}).get("summary", {}).get("total_count", 0)
                        }

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
                "total_posts": len(posts_data),
                "total_reels": len(reels_data),
                "cover_image": {
                    "id": cover_id,
                    "source": cover_image_url,
                    "created_time": cover_created_time,
                    "caption": cover_caption,
                    "engagement": cover_engagement
                },
                "posts": [
                    {
                        "id": post.get("id"),
                        "message": post.get("message"),
                        "created_time": post.get("created_time"),
                        "permalink_url": post.get("permalink_url"),
                        "image_url": post.get("image_url", ""),
                        "likes_count": post.get("likes_count", 0),
                        "reactions_count": post.get("reactions_count", 0),
                        "comments_count": post.get("comments_count", 0),
                        "shares_count": post.get("shares_count", 0),
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
