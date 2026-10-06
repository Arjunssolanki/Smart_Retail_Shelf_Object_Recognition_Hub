import os
import mysql.connector

class IngestionAgent:
    def __init__(self):
        self.config = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME")
        }

    def load_to_bronze_layer(self, file_key, validated_data):
        conn = mysql.connector.connect(**self.config)
        cursor = conn.cursor()
        insert_query = """
            INSERT INTO bronze_shelf_detections (
                store_id, client_number, image_filename, detected_brand, detected_product, confidence_score,
                x_center, y_center, bbox_width, bbox_height
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for item in validated_data:
            cursor.execute(insert_query, (
                "STORE_MOCK_99",
                "CLI_MOCK_88",
                file_key,
                str(item["detected_brand"]),
                str(item["detected_product"]),
                float(item["confidence"]),
                float(item["x_center"]),
                float(item["y_center"]),
                float(item["width"]),
                float(item["height"])
            ))
        conn.commit()
        cursor.close()
        conn.close()
