import os
import json
import requests
from flask import Blueprint, jsonify
from config import Config  # Ensure Config has PAGE_ACCESS_TOKEN and AD_ACCOUNT_ID

JSON_FILE_PATH = "meta_ads.json"

meta_ads_blueprint = Blueprint('meta_ads', __name__)

@meta_ads_blueprint.route('/meta-ads', methods=['GET'])
def get_meta_ads_data():
    """Fetches Facebook Ads and Instagram Ads data using Ad Account ID and saves it to a JSON file."""
    try:
        ad_account_id = Config.AD_ACCOUNT_ID  # Use the ad account ID from your config file
        access_token = Config.PAGE_ACCESS_TOKEN  # Your Page Access Token

        # Step 1: Fetch ads data from the Ad Account
        ads_url = f"https://graph.facebook.com/v18.0/{ad_account_id}/ads"
        ads_params = {
            "fields": "id,name,adset_id,campaign_id,status",  # Basic ad fields
            "access_token": access_token
        }

        ads_response = requests.get(ads_url, params=ads_params)

        if not ads_response.ok:
            return jsonify({"error": "Failed to fetch Ads", "details": ads_response.text}), ads_response.status_code

        ads_data = ads_response.json().get('data', [])
        if not ads_data:
            return jsonify({"error": "No ads found in the Ad Account"}), 404

        campaign_ads_data = []

        for ad in ads_data:
            ad_id = ad.get("id")

            # Step 2: Fetch insights for each ad with valid fields and platform breakdown
            insights_url = f"https://graph.facebook.com/v18.0/{ad_id}/insights"
            insights_params = {
                "fields": "campaign_name,reach,impressions,spend,clicks,frequency,date_start,date_stop,cpm,cpc,ctr",  # Basic insights fields
                "breakdown": "publisher_platform",  # Breakdown by platform (Facebook, Instagram, Audience Network)
                "access_token": access_token
            }

            insights_response = requests.get(insights_url, params=insights_params)

            if insights_response.ok:
                insights_data = insights_response.json().get('data', [])
                if insights_data:
                    ad["insights"] = insights_data
                    # Debugging: Print all the available fields in the insights data
                    print(f"Insight Data for Ad ID: {ad_id}")
                    for insight in insights_data:
                        for key, value in insight.items():
                            print(f"{key}: {value}")  # Print each key-value pair in insights

                    # Process the insights data to format it with platforms (Facebook, Instagram, Audience Network)
                    platform_data = {}
                    for insight in insights_data:
                        platform = insight.get('publisher_platform', 'unknown')  # Default to 'unknown' if platform is missing or null
                        print(f"Platform for Ad ID {ad_id}: {platform}")  # Debug print for platform
                        if platform not in platform_data:
                            platform_data[platform] = []
                        platform_data[platform].append(insight)

                    ad["insights_by_platform"] = platform_data
                else:
                    ad["insights"] = "No insights available"
            else:
                ad["insights"] = f"Failed to fetch insights: {insights_response.text}"

            campaign_ads_data.append(ad)

        # Save data to JSON file
        with open(JSON_FILE_PATH, "w") as json_file:
            json.dump({"ads_data": campaign_ads_data}, json_file, indent=4)

        return jsonify({"message": "Meta Ads data saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@meta_ads_blueprint.route('/saved-meta-ads', methods=['GET'])
def get_saved_meta_ads():
    """Returns saved Meta Ads data from the JSON file."""
    print("Frontend requested saved Meta Ads data")  # Debugging statement

    if not os.path.exists(JSON_FILE_PATH):
        return jsonify({"error": "No saved data found"}), 404

    with open(JSON_FILE_PATH, "r") as json_file:
        data = json.load(json_file)

    return jsonify(data), 200
