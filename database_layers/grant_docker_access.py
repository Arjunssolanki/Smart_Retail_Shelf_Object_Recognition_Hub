import os
import mysql.connector
from dotenv import load_dotenv

def main():
    # Load all environment variables from your root .env file
    load_dotenv()
    
    db_password = os.getenv("DB_PASSWORD")
    db_user = os.getenv("DB_USER", "root")
    
    if not db_password:
        print("❌ Error: DB_PASSWORD not found inside your .env configuration file.")
        return
        
    print("🔒 Safely reading database credentials from your .env configuration wrapper...")
    
    try:
        # FIX: Force host="localhost" so this script connects directly from your Windows machine
        # even if DB_HOST inside the .env file is set to 'host.docker.internal' for Docker containers.
        conn = mysql.connector.connect(
            host="localhost",
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()
        
        # Dynamically create the user and grant access to the Docker bridge network gateway
        grant_query_1 = f"CREATE USER IF NOT EXISTS 'root'@'host.docker.internal' IDENTIFIED BY '{db_password}';"
        grant_query_2 = "GRANT ALL PRIVILEGES ON *.* TO 'root'@'host.docker.internal' WITH GRANT OPTION;"
        flush_query = "FLUSH PRIVILEGES;"
        
        cursor.execute(grant_query_1)
        cursor.execute(grant_query_2)
        cursor.execute(flush_query)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 SUCCESS: Host database network bridge privileges cleanly granted to host.docker.internal!")
        
    except mysql.connector.Error as e:
        print(f"❌ Database Administration Error: {str(e)}")

if __name__ == "__main__":
    main()
