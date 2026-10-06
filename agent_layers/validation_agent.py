import os
import json
import re
import requests

class ValidationAgent:
    def __init__(self):
        self.jev_api_key = os.getenv("JEV_AI_API_KEY")
        self.jev_url = "https://jev.ai"

    def parse_and_validate_json(self, raw_text):
        if not raw_text:
            return None
        
        raw_text = raw_text.strip()
        
        # Step 1: Direct Parsing Attempt
        try:
            return json.loads(raw_text)
        except Exception:
            pass
            
        # Step 2: Extract bracket contents and automatically fix truncation anomalies
        try:
            start_idx = raw_text.find("[")
            if start_idx == -1:
                return None
                
            array_content = raw_text[start_idx:]
            
            # Find the last valid closed object block matching structural syntax boundaries
            valid_objects = re.findall(r'\{[^{}]*?\}', array_content)
            if not valid_objects:
                return None
                
            # Reconstruct a clean, closed JSON array structure dynamically
            reconstructed_json_str = "[" + ",".join(valid_objects) + "]"
            return json.loads(reconstructed_json_str)
        except Exception:
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
            "context": "Validate open retail product variables. Strip out formatting noise and return a clean array."
        }
        
        try:
            response = requests.post(self.jev_url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json().get("enriched_records", detections)
        except Exception:
            return detections
        return detections

    def filter_malformed_records(self, detections):
        required_keys = {"detected_brand", "detected_product", "confidence", "x_center", "y_center", "width", "height"}
        valid_records = []
        if not isinstance(detections, list):
            return valid_records
        for item in detections:
            if isinstance(item, dict) and required_keys.issubset(item.keys()):
                valid_records.append(item)
        return valid_records
