import os
import kagglehub
from dotenv import load_dotenv

# 1. Load the access token from your secure .env file
load_dotenv()

# 2. Assign the specific Kaggle API Token environment variable
os.environ["KAGGLE_API_TOKEN"] = os.getenv("KAGGLE_API_TOKEN")

print("Authenticating with Kaggle via Access Token and starting download...")
try:
    # 3. Pull the compact dataset mirror down to your local cache
    path = kagglehub.dataset_download("singhalsandb/sku110k")
    print(f"Download complete! Data cache location: {path}")
except Exception as e:
    print(f"An execution error occurred: {e}")
