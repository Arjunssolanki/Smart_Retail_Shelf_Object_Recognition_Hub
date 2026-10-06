import os
import json
import requests

class ValidationAgent:
    def __init__(self):
        self.jev_api_key = os.getenv("JEV_AI_API_KEY")
        self.jev_url = "https://jev.ai"

    def parse_and_validate_json(self, raw_text):
        try:
            return json.loads(raw_text)
        except Exception:
            if "[" in raw_text and "]" in raw_text:
                start = raw_text.find("[")
                end = raw_text.rfind("]") + 1
                try:
                    return json.loads(raw_text[start:end])
                except Exception:
                    return None
            return None

    def enrich_catalog_with_jev_ai(self, detections):
        if not self.jev_api_key:
            return detections
            
        headers = {
            "Authorization": f"Bearer {self.jev_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "records": detections,
            "context": "Validate and map granular retail product variations. Ensure that distinct flavors and variants (like Yellow bags for Lay's Classic Salted vs Green bags for Lay's Cream & Onion vs Red/Green Pringles cans) keep their unique class_ids (2, 3, 4, 5, 6) intact. Prevent the consolidation of distinct items into a single fallback brand label."
        }
        
        try:
            response = requests.post(self.jev_url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json().get("enriched_records", detections)
        except Exception:
            return detections
        return detections

    def filter_malformed_records(self, detections):
        required_keys = {"class_id", "confidence", "x_center", "y_center", "width", "height"}
        valid_records = []
        if not isinstance(detections, list):
            return valid_records
        for item in detections:
            if isinstance(item, dict) and required_keys.issubset(item.keys()):
                valid_records.append(item)
        return valid_records
