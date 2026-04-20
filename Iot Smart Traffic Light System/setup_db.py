import sqlite3
from werkzeug.security import generate_password_hash

def setup_database():
    try:
        conn = sqlite3.connect('smart_traffic_light.db')
        cursor = conn.cursor()

        # Read and execute schema.sql
        with open('schema.sql', 'r') as file:
            sql_script = file.read()
        
        cursor.executescript(sql_script)
        
        # Create admin user
        admin_username = "admin"
        admin_password = "password" # Hardcoded for simple setup, they can change it later
        hashed_password = generate_password_hash(admin_password)

        cursor.execute("INSERT OR REPLACE INTO users (username, password_hash) VALUES (?, ?)", (admin_username, hashed_password))
        conn.commit()
        print(f"Database setup complete. Admin user '{admin_username}' created with password '{admin_password}'.")

    except sqlite3.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    setup_database()
