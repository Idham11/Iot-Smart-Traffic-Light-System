import os
import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable not set. Please create a .env file.")
        return

    try:
        url = urlparse(db_url)
        # We need to enable multiple statements for our schema.sql
        from pymysql.constants import CLIENT
        
        conn = pymysql.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            database=url.path[1:],
            port=url.port or 3306,
            client_flag=CLIENT.MULTI_STATEMENTS
        )
        cursor = conn.cursor()

        print("Connected to database. Executing schema...")
        # Read and execute schema.sql
        with open('schema.sql', 'r') as file:
            sql_script = file.read()
        
        # pymysql can execute multiple statements if MULTI_STATEMENTS flag is set
        cursor.execute(sql_script)
        
        # Create admin user
        admin_username = "admin"
        admin_password = "password" # Hardcoded for simple setup, they can change it later
        hashed_password = generate_password_hash(admin_password)

        # MySQL uses INSERT IGNORE or ON DUPLICATE KEY UPDATE instead of INSERT OR REPLACE
        cursor.execute("""
            INSERT IGNORE INTO users (username, password_hash) 
            VALUES (%s, %s)
        """, (admin_username, hashed_password))
        
        conn.commit()
        print(f"Database setup complete. Admin user '{admin_username}' created with password '{admin_password}'.")

    except Exception as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    setup_database()
