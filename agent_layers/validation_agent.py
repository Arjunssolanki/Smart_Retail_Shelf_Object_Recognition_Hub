import json

class ValidationAgent:
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

    def filter_malformed_records(self, detections):
        required_keys = {"class_id", "confidence", "x_center", "y_center", "width", "height"}
        valid_records = []
        if not isinstance(detections, list):
            return valid_records
        for item in detections:
            if isinstance(item, dict) and required_keys.issubset(item.keys()):
                valid_records.append(item)
        return valid_records
