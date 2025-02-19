import os
import json
import requests
from flask import Blueprint, jsonify
from config import Config  # Ensure Config has PAGE_ACCESS_TOKEN and AD_ACCOUNT_ID

JSON_FILE_PATH = "meta_ads3.json"

insta_ads_blueprint = Blueprint('insta-ads', __name__)

# Fields for Insights API
insight_fields = [
    "account_id", "account_name", "ad_id", "ad_name", "adset_id", "adset_name",
    "campaign_id", "campaign_name", "clicks", "cpc", "cpm", "cpp", "ctr", 
    "date_start", "date_stop", "engagement_rate_ranking", "frequency",
    "impressions", "inline_link_clicks", "inline_post_engagement", "objective",
    "quality_ranking", "reach", "social_spend", "spend", 
    "unique_clicks", "unique_ctr",  
    "video_p100_watched_actions", "video_p25_watched_actions",
    "video_p50_watched_actions", "video_p75_watched_actions", "video_p95_watched_actions"
]

# Breakdown Fields
breakdown_fields = "age,gender,device_platform,region"

@insta_ads_blueprint.route('/insta-ads', methods=['GET'])
def fetch_all_campaign_insights():
    try:
        ad_account_id = Config.AD_ACCOUNT_ID
        access_token = Config.PAGE_ACCESS_TOKEN

        # Step 1: Fetch all ads
        ads_url = f"https://graph.facebook.com/v18.0/{ad_account_id}/ads"
        ads_params = {
            "fields": "id,name,adset_id,campaign_id,status",
            "access_token": access_token
        }
        ads_response = requests.get(ads_url, params=ads_params)

        if not ads_response.ok:
            return jsonify({"error": "Failed to fetch Ads", "details": ads_response.text}), ads_response.status_code

        ads_data = ads_response.json().get('data', [])
        if not ads_data:
            return jsonify({"error": "No ads found"}), 404

        campaign_ads_data = []

        # Step 2: Fetch insights for each ad, filtering for Instagram platform only
        for ad in ads_data:
            ad_id = ad.get("id")
            insights_url = f"https://graph.facebook.com/v18.0/{ad_id}/insights"
            insights_params = {
                "fields": ",".join(insight_fields),
                "breakdowns": breakdown_fields,
                "publisher_platform": "instagram",
                "access_token": access_token
            }

            insights_response = requests.get(insights_url, params=insights_params)

            if insights_response.ok:
                insights_data = insights_response.json().get('data', [])
                ad["insights"] = insights_data if insights_data else "No insights available"
            else:
                ad["insights"] = f"Failed to fetch insights: {insights_response.text}"

            # Step 3: Fetch breakdown insights only for Instagram (age, region, gender, device)
            breakdown_insights = fetch_breakdown_insights(ad_account_id, access_token)
            ad["breakdown_insights"] = breakdown_insights

            campaign_ads_data.append(ad)

        # Step 4: Save data to JSON
        with open(JSON_FILE_PATH, "w") as json_file:
            json.dump({"ads_data": campaign_ads_data}, json_file, indent=4)

        return jsonify({"message": "Meta Ads data saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@insta_ads_blueprint.route('/saved-meta-ads3', methods=['GET'])
def get_saved_meta_ads():
    """Returns saved Meta Ads data from the JSON file."""
    if not os.path.exists(JSON_FILE_PATH):
        return jsonify({"error": "No saved data found"}), 404
    
    with open(JSON_FILE_PATH, "r") as json_file:
        data = json.load(json_file)
    return jsonify(data), 200
def fetch_breakdown_insights(ad_account_id, access_token):
    """Fetch breakdown insights for Instagram (Age, Region, Gender, Device Platform) manually filtering results."""
    BASE_URL = f"https://graph.facebook.com/v18.0/{ad_account_id}/insights"

    COMMON_PARAMS = {
        'access_token': access_token,
        'fields': 'reach,impressions,clicks',
        'date_preset': 'maximum',
    }

    BREAKDOWNS = ['age', 'region', 'gender', 'device_platform']
    breakdown_data = {}

    for breakdown in BREAKDOWNS:
        params = COMMON_PARAMS.copy()
        params['breakdowns'] = breakdown

        all_data = []
        while True:
            response = requests.get(BASE_URL, params=params)
            if not response.ok:
                breakdown_data[breakdown] = {"error": response.text}
                break

            data = response.json()
            if 'data' in data:
                # Filter to include only Instagram data
                instagram_data = [entry for entry in data['data'] if entry.get("publisher_platform") == "instagram"]
                all_data.extend(instagram_data)
            else:
                breakdown_data[breakdown] = {"error": "No data available"}
                break

            # Handle pagination
            if 'paging' in data and 'next' in data['paging']:
                params['after'] = data['paging']['cursors']['after']
            else:
                breakdown_data[breakdown] = all_data
                break

    return breakdown_data
