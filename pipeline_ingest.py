from dotenv import load_dotenv
from agent_layers.perception_agent import PerceptionAgent
from agent_layers.validation_agent import ValidationAgent
from agent_layers.ingestion_agent import IngestionAgent

def run_coordinated_pipeline():
    load_dotenv()
    
    perception = PerceptionAgent()
    validator = ValidationAgent()
    ingestion = IngestionAgent()
    
    file_key = perception.get_latest_image_key()
    if not file_key:
        return
        
    base64_frame = perception.fetch_and_encode_image(file_key)
    raw_ai_output = perception.run_vision_inference(base64_frame)
    
    raw_json = validator.parse_and_validate_json(raw_ai_output)
    if not raw_json:
        return
        
    clean_records = validator.filter_malformed_records(raw_json)
    if not clean_records:
        return
        
    ingestion.load_to_bronze_layer(file_key, clean_records)

if __name__ == "__main__":
    run_coordinated_pipeline()
