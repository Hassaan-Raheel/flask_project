import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "your_default_token")
    PAGE_ID = os.getenv("PAGE_ID", "your_default_page_id")
    INSTAGRAM_PAGE_ID = os.getenv("INSTAGRAM_PAGE_ID", "your_default_instagram_page_id")
