# 🚁 Real-Time MAVLink GPS Tracker

This project provides a **simple yet powerful ground station system** to visualize a drone's GPS position on a map in **real-time**.  
It works seamlessly with **PX4 SITL (Software-In-The-Loop)** for testing and can be easily adapted for **real hardware**.

---

## 📦 System Components

1. **Python Backend (`gcs_server.py`)**  
   - Flask server that connects to a MAVLink source.  
   - Parses `GLOBAL_POSITION_INT` messages.  
   - Relays GPS data via **WebSockets**.

2. **HTML Frontend (`index.html`)**  
   - Single-page web app using **Leaflet.js**.  
   - Renders a live map with drone position and flight path.

3. **Mission Generator (`mission_generator.py`)**  
   - Python script to create a pre-planned mission file.  
   - Automatically uploads it to SITL for autonomous flight.

---

## ⚙️ How to Use

### 1. Prerequisites

Ensure you have **Python 3** and the required packages installed:

```bash
# Install required Python packages
pip install pymavlink Flask flask-socketio
```
Clone the PX4 Autopilot repository for SITL:

```bash

git clone https://github.com/PX4/PX4-Autopilot.git --recursive
cd PX4-Autopilot
```
2. Running the System
Step 1: Start the Ground Station Backend
```bash

# In project directory
python gcs_server.py
```
You should see logs like:
```
MAVLink Heartbeat received! Connection established. once PX4 is broadcasting.
```

Step 2: Start PX4 SITL Simulation
```bash

# Inside PX4-Autopilot directory
make px4_sitl jmavsim
```
PX4 will broadcast MAVLink on udp:127.0.0.1:14550.
The backend will automatically connect.

Step 3: Open the Ground Station Map
Open your browser and visit:

```bash

http://127.0.0.1:5000
```
Once GPS lock is established, you’ll see the drone’s live position on the map.

3. Creating & Running a Mission
Step 1: Generate & Upload Mission
```bash

# In project directory
python mission_generator.py --upload
```
This creates mission.txt and uploads it to SITL.
You should see: Mission upload successful!.

Step 2: Start Mission in SITL
In the PX4 SITL console (pxh>), run:

```bash

commander mode auto:mission
commander arm
```
The drone will:
✅ Arm
✅ Takeoff
✅ Fly the square mission pattern

You can watch it in real-time on the ground station map.