import pandas as pd
import os
import json
from flask import Flask, jsonify, Blueprint

google_ads_blueprint = Blueprint('google_ads', __name__)

UPLOAD_FOLDER = 'uploads'  # Directory where CSV files are stored
GOOGLE_ADS_CSV = os.path.join(UPLOAD_FOLDER, 'data.csv')
CAMPAIGN_CSV = os.path.join(UPLOAD_FOLDER, 'campaign.csv')

@google_ads_blueprint.route('/google-ads', methods=['GET'])
def get_google_ads_data():
    return get_cleaned_csv_data(GOOGLE_ADS_CSV)

@google_ads_blueprint.route('/campaign-data', methods=['GET'])
def get_campaign_data():
    return get_filtered_campaign_data(CAMPAIGN_CSV)

def get_cleaned_csv_data(csv_file):
    """Processes CSV file, cleans data, and returns JSON."""
    try:
        if not os.path.exists(csv_file):
            return jsonify({"error": f"File {csv_file} not found"}), 404

        df = pd.read_csv(csv_file, skiprows=1, dtype=str)  # Read as strings to avoid type issues
        df = df.dropna(axis=1, how='all')  # Drop empty columns
        df.columns = df.iloc[0].fillna('')  # Assign second row as header, replace NaNs
    # Remove the header row from data
        df = df[1:].reset_index(drop=True) 

        return jsonify(df.to_dict(orient='records'))

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def get_filtered_campaign_data(csv_file):
    """Processes campaign.csv, filters data by date, converts to JSON, and prints it."""
    try:
        if not os.path.exists(csv_file):
            return jsonify({"error": f"File {csv_file} not found"}), 404

        # Read CSV and handle errors
        df = pd.read_csv(csv_file, skiprows=2, dtype=str, keep_default_na=False)  # Assign third row as header
        df = df.dropna(axis=1, how='all')  # Drop empty columns
        df.columns = df.columns.str.strip()  # Remove extra spaces from column names
        
        # Convert DataFrame to JSON
        data = df.to_dict(orient='records')

        # Print JSON in console
        print(json.dumps(data, indent=4))  

        # Return JSON response
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
       

   