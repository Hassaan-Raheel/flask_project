import os
import json
import requests
from flask import Blueprint, jsonify
from config import Config  # Ensure Config has PAGE_ACCESS_TOKEN and AD_ACCOUNT_ID

JSON_FILE_PATH = "meta_ads2.json"

ads_reports_blueprint = Blueprint('ads-Report', __name__)

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

# Additional breakdowns for Age, Gender, Device, and Region
breakdown_fields = "age,gender,device_platform,region"

@ads_reports_blueprint.route('/ads-Report', methods=['GET'])
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

        # Step 2: Fetch insights for each ad
        for ad in ads_data:
            ad_id = ad.get("id")
            insights_url = f"https://graph.facebook.com/v18.0/{ad_id}/insights"
            insights_params = {
    "fields": "account_id,account_name,ad_id,ad_name,adset_id,adset_name,"
              "campaign_id,campaign_name,clicks,cpc,cpm,cpp,ctr,"
              "date_start,date_stop,engagement_rate_ranking,frequency,"
              "impressions,inline_link_clicks,inline_post_engagement,objective,"
              "quality_ranking,reach,social_spend,spend,"
              "unique_clicks,unique_ctr,"
              "video_p100_watched_actions,video_p25_watched_actions,"
              "video_p50_watched_actions,video_p75_watched_actions,video_p95_watched_actions",
    "breakdowns": "publisher_platform",  # Breakdown by platform (Facebook, Instagram, Audience Network)
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

            # Fetch additional breakdown insights (Age, Region, Gender, Device)
            breakdown_insights = fetch_breakdown_insights(ad_account_id, access_token)
            ad["breakdown_insights"] = breakdown_insights  # Add breakdown data to ad insights

            campaign_ads_data.append(ad)


        # Step 4: Save data to JSON
        with open(JSON_FILE_PATH, "w") as json_file:
            json.dump({"ads_data": campaign_ads_data}, json_file, indent=4)

        return jsonify({"message": "Meta Ads data saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@ads_reports_blueprint.route('/saved-meta-ads2', methods=['GET'])
def get_saved_meta_ads():
    """Returns saved Meta Ads data from the JSON file."""
    if not os.path.exists(JSON_FILE_PATH):
        return jsonify({"error": "No saved data found"}), 404

    with open(JSON_FILE_PATH, "r") as json_file:
        data = json.load(json_file)

    return jsonify(data), 200


def fetch_breakdown_insights(ad_account_id, access_token):
    """Fetch insights separately for Age, Region, Gender, and Device Platform with pagination."""
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
            data = response.json()

            if 'data' in data:
                all_data.extend(data['data'])
            else:
                breakdown_data[breakdown] = {"error": "No data or error in response"}
                break

            if 'paging' in data and 'next' in data['paging']:
                params['after'] = data['paging']['cursors']['after']
            else:
                breakdown_data[breakdown] = all_data
                break

    return breakdown_data
