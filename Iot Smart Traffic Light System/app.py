import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
from werkzeug.security import check_password_hash
import pymysql.cursors
from urllib.parse import urlparse
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


# Import hardware and camera modules
from hardware import traffic_controller
from camera import camera_stream, generate_frames

app = Flask(__name__)
# In production, use a strong, random secret key
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_for_development')
app.permanent_session_lifetime = timedelta(minutes=30)

def get_db_connection():
    try:
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            print("DATABASE_URL environment variable not set. Please set it in .env file.")
            return None
            
        url = urlparse(db_url)
        conn = pymysql.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            database=url.path[1:],
            port=url.port or 3306,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as err:
        print(f"Error connecting to database: {err}")
        return None

def log_system_event(event_type, description):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO system_logs (event_type, description) VALUES (%s, %s)",
                (event_type, description)
            )
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Failed to log event: {e}")
        finally:
            conn.close()

def log_decision(counts, selected_lane, priority_score, green_duration, reason):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO decision_logs 
                (lane_a_count, lane_b_count, lane_c_count, selected_lane, priority_score, green_duration, reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (counts.get('A', 0), counts.get('B', 0), counts.get('C', 0), selected_lane, priority_score, green_duration, reason))
            conn.commit()
        except Exception as e:
            print(f"Failed to log decision: {e}")
        finally:
            conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user and check_password_hash(user['password_hash'], password):
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                log_system_event('LOGIN', f"User {username} logged in")
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
        else:
            flash('Database connection failed', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('username')
    if username:
        log_system_event('LOGOUT', f"User {username} logged out")
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/video_feed')
def video_feed():
    if 'user_id' not in session:
        return "Unauthorized", 401
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def status():
    """API endpoint to get current traffic light and sensor status"""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get real data from hardware controller
    status_data = traffic_controller.get_status()
    
    # Fetch recent decisions for the dashboard logs
    conn = get_db_connection()
    recent_logs = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM decision_logs ORDER BY timestamp DESC LIMIT 10")
        rows = cursor.fetchall()
        for row in rows:
            recent_logs.append(dict(row))
        conn.close()
        
    status_data['recent_logs'] = recent_logs
    return jsonify(status_data)

if __name__ == '__main__':
    # Bind the decision logger
    traffic_controller.set_decision_callback(log_decision)
    
    # Start the camera stream
    camera_stream.start()
    
    print("Starting server...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
