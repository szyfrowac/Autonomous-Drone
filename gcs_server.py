# gcs_server.py
# This script creates a Flask web server that connects to a MAVLink source (like PX4 SITL),
# reads GPS data, and broadcasts it to a web client via Socket.IO.

import time
import os
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from pymavlink import mavutil

# --- Configuration ---
# MAVLink connection string
# For SITL (Software in the Loop) simulation:
MAVLINK_CONNECTION_STRING = 'udp:127.0.0.1:14551'
# For a real telemetry radio via USB:
# MAVLINK_CONNECTION_STRING = '/dev/ttyUSB0' # Linux/Mac
# MAVLINK_CONNECTION_STRING = 'COM3' # Windows (replace COM3 with your port)

# --- Flask App and SocketIO Initialization ---
app = Flask(__name__, static_folder='static', template_folder='templates')
# Use a secret key for session management
app.config['SECRET_KEY'] = 'a_very_secret_key_that_should_be_changed'
socketio = SocketIO(app, async_mode='threading')

# Global variable to hold the MAVLink connection
master = None

# --- MAVLink Connection and Data Reading Thread ---
def mavlink_thread():
    """
    Connects to the MAVLink source and continuously reads messages.
    When a GLOBAL_POSITION_INT message is received, it emits the GPS data
    to the connected web clients.
    """
    global master
    print(f"Attempting to connect to MAVLink at: {MAVLINK_CONNECTION_STRING}")

    while True:
        try:
            # Establish MAVLink connection
            master = mavutil.mavlink_connection(MAVLINK_CONNECTION_STRING)
            # Wait for the first heartbeat to confirm connection
            master.wait_heartbeat()
            print("MAVLink Heartbeat received! Connection established.")
            socketio.emit('status_update', {'message': 'MAVLink Connected'})

            # Main loop to receive messages
            while True:
                # Wait for any MAVLink message with a timeout. This is more robust.
                msg = master.recv_match(blocking=True, timeout=5)

                # If no message received in 5 seconds, the connection might be lost.
                if not msg:
                    print("MAVLink connection timed out. Reconnecting...")
                    socketio.emit('status_update', {'message': 'MAVLink Timeout. Reconnecting...'})
                    break # Break inner loop to trigger reconnection

                # Check if the message is the specific GPS data we are interested in.
                if msg.get_type() == 'GLOBAL_POSITION_INT':
                    # Data from GLOBAL_POSITION_INT message
                    # Latitude and Longitude are in degrees * 1e7
                    lat = msg.lat / 1e7
                    lon = msg.lon / 1e7
                    # Altitude is in millimeters
                    alt = msg.relative_alt / 1000.0  # Convert to meters

                    # Prepare data payload
                    gps_data = {
                        'lat': lat,
                        'lon': lon,
                        'alt': round(alt, 2)
                    }
                    # Emit data to all connected clients
                    socketio.emit('gps_update', gps_data)
                    # print(f"Sent GPS data: {gps_data}") # Uncomment for debugging
        
        except Exception as e:
            print(f"MAVLink connection error: {e}")
            socketio.emit('status_update', {'message': f'MAVLink Error: {e}'})
        
        finally:
            if master:
                master.close()
            master = None
            print("Connection closed. Retrying in 5 seconds...")
            time.sleep(5) # Wait before trying to reconnect


# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    """Serves static files (for CSS, JS if you add them later)."""
    return send_from_directory('static', path)


# --- SocketIO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    """Handles a new client connection."""
    print('Client connected')
    if master and master.target_system:
        socketio.emit('status_update', {'message': 'MAVLink Connected'})
    else:
        socketio.emit('status_update', {'message': 'Attempting to connect to MAVLink...'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handles a client disconnection."""
    print('Client disconnected')


# --- Main Execution ---
if __name__ == '__main__':
    print("Starting MAVLink data reader thread...")
    socketio.start_background_task(mavlink_thread)
    
    print("Starting Flask-SocketIO server at http://127.0.0.1:5000")
    # Use allow_unsafe_werkzeug=True for newer versions of Werkzeug
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
