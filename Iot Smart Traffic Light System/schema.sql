-- Table to store user credentials
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to log traffic system events and statuses
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(50) NOT NULL, -- e.g., 'LOGIN', 'TRAFFIC_LIGHT_UPDATE', 'VEHICLE_DETECTED'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to log traffic decisions based on priority algorithm
CREATE TABLE IF NOT EXISTS decision_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lane_a_count INTEGER NOT NULL,
    lane_b_count INTEGER NOT NULL,
    lane_c_count INTEGER NOT NULL,
    selected_lane VARCHAR(10) NOT NULL,
    priority_score INTEGER NOT NULL,
    green_duration INTEGER NOT NULL,
    reason TEXT
);
