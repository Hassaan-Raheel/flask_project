import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "your_default_token")
    PAGE_ID = os.getenv("PAGE_ID", "your_default_page_id")
    INSTAGRAM_PAGE_ID = os.getenv("INSTAGRAM_PAGE_ID", "your_default_instagram_page_id")
    AD_ACCOUNT_ID = os.getenv('AD_ACCOUNT_ID', 'act_402130546896771')  # Replace with your actual Ad Account ID
