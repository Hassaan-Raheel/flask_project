import os
import json
import requests
from flask import Blueprint, jsonify
from config import Config  # Ensure Config has PAGE_ACCESS_TOKEN and AD_ACCOUNT_ID

JSON_FILE_PATH = "meta_ads4.json"

meta_ads_blueprint = Blueprint('meta_ads', __name__)

@meta_ads_blueprint.route('/meta-ads4', methods=['GET'])
def get_meta_ads_data():
    """Fetches Facebook Ads and Instagram Ads data using Ad Account ID and saves it to a JSON file."""
    try:
        ad_account_id = Config.AD_ACCOUNT_ID  
        access_token = Config.PAGE_ACCESS_TOKEN  

        # Step 1: Fetch ads data from the Ad Account with pagination
        ads_url = f"https://graph.facebook.com/v18.0/{ad_account_id}/ads"
        ads_params = {
            "fields": "id,name,adset_id,campaign_id,status",
            "access_token": access_token
        }

        ads_data = []
        while True:
            ads_response = requests.get(ads_url, params=ads_params)

            if not ads_response.ok:
                return jsonify({"error": "Failed to fetch Ads", "details": ads_response.text}), ads_response.status_code

            page_data = ads_response.json().get('data', [])
            if page_data:
                ads_data.extend(page_data)  
            else:
                break  

            if 'paging' in ads_response.json() and 'next' in ads_response.json()['paging']:
                ads_url = ads_response.json()['paging']['next']  
            else:
                break  

        if not ads_data:
            return jsonify({"error": "No ads found in the Ad Account"}), 404

        campaign_ads_data = []

        for ad in ads_data:
            ad_id = ad.get("id")
            campaign_id = ad.get("campaign_id")

            # Fetch campaign duration
            if campaign_id:
                ad["campaign_duration"] = get_campaign_details(campaign_id, access_token)
            else:
                ad["campaign_duration"] = "No campaign ID available"

            # Step 2: Fetch insights for each ad with valid fields and platform breakdown
            insights_url = f"https://graph.facebook.com/v18.0/{ad_id}/insights"
            insights_params = {
                "fields": "campaign_name,reach,impressions,spend,clicks,frequency,cpm,cpc,ctr",
                "breakdown": "publisher_platform",
                "access_token": access_token
            }

            insights_data = []
            while True:
                insights_response = requests.get(insights_url, params=insights_params)

                if insights_response.ok:
                    page_data = insights_response.json().get('data', [])
                    if page_data:
                        insights_data.extend(page_data)  
                    else:
                        break  

                    if 'paging' in insights_response.json() and 'next' in insights_response.json()['paging']:
                        insights_url = insights_response.json()['paging']['next']  
                    else:
                        break  
                else:
                    ad["insights"] = f"Failed to fetch insights: {insights_response.text}"
                    break  

            if insights_data:
                ad["insights"] = insights_data
                platform_data = {}
                for insight in insights_data:
                    platform = insight.get('publisher_platform', 'unknown')  
                    if platform not in platform_data:
                        platform_data[platform] = []
                    platform_data[platform].append(insight)

                ad["insights_by_platform"] = platform_data
            else:
                ad["insights"] = "No insights available"

            # Fetch additional breakdown insights (Age, Region, Gender, Device)
            breakdown_insights = fetch_breakdown_insights(ad_account_id, access_token)
            ad["breakdown_insights"] = breakdown_insights  

            campaign_ads_data.append(ad)

        # Save data to JSON file
        with open(JSON_FILE_PATH, "w") as json_file:
            json.dump({"ads_data": campaign_ads_data}, json_file, indent=4)

        return jsonify({"message": "Meta Ads data saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500
    

@meta_ads_blueprint.route('/saved-meta-ads4', methods=['GET'])
def get_saved_meta_ads():
    """Returns saved Meta Ads data from the JSON file."""
    print("Frontend requested saved Meta Ads data")  

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
                BASE_URL = data['paging']['next']  
            else:
                breakdown_data[breakdown] = all_data
                break

    return breakdown_data

def get_campaign_details(campaign_id, access_token):
    """Fetch campaign start and stop times to determine duration."""
    url = f"https://graph.facebook.com/v18.0/{campaign_id}"
    params = {
        "fields": "start_time,stop_time",
        "access_token": access_token
    }

    response = requests.get(url, params=params)
    if response.ok:
        data = response.json()
        start_time = data.get("start_time", "Unknown")
        stop_time = data.get("stop_time", "Ongoing")

        return f"{start_time} to {stop_time}" if start_time and stop_time else f"Started on {start_time} (Ongoing)"
    
    return "Failed to fetch campaign details"
