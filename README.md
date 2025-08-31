# Real-Time MAVLink GPS Tracker

This project provides a simple yet powerful ground station system to visualize a drone's GPS position on a map in real-time. It's designed to work seamlessly with PX4 SITL (Software-In-The-Loop) for testing and can be easily adapted for real hardware.

The system consists of three main components:

1. Python Backend (gcs_server.py): A Flask server that connects to a MAVLink source, parses GLOBAL_POSITION_INT messages, and relays the data via WebSockets.

2. HTML Frontend (index.html): A single-page web application that uses Leaflet.js to render a map and plots the drone's position and flight path.

3. Python Mission Generator (mission_generator.py): A script to create a pre-planned flight mission file and automatically upload it to the simulator.

# How to Use
1. Prerequisites
First, ensure you have Python and the necessary libraries installed.

# Make sure you have Python 3 installed
# Install required Python packages
```
pip install pymavlink Flask flask-socketio
```

You will also need to have the PX4 Autopilot repository cloned to run the SITL simulation. If you don't have it, clone it from the official repository:

git clone [https://github.com/PX4/Autopilot.git](https://github.com/PX4/Autopilot.git) --recursive
cd Autopilot

2. Running the System
Follow these steps in order:

Step 1: Start the Ground Station Backend

Open a terminal, navigate to the directory where you saved the project files, and run the Python script:

python gcs_server.py

You should see output indicating that the server is running and attempting to connect to MAVLink.

Step 2: Start the PX4 SITL Simulation

Open a new, separate terminal, navigate to your Autopilot directory, and start the simulation.

# Make sure you are in the PX4-Autopilot directory
make px4_sitl jmavsim

Once the simulation is running, it will automatically start broadcasting MAVLink data on udp:127.0.0.1:14550. The backend terminal should now show "MAVLink Heartbeat received! Connection established."

Step 3: View the Map in Your Browser

Open your web browser (Chrome, Firefox, etc.) and navigate to:

http://127.0.0.1:5000

The webpage will load, and as soon as the simulator gets a GPS lock, you will see the drone's position appear on the map.

3. Creating and Running a Mission
You can now generate and upload a mission file to have the simulated drone fly autonomously.

Step 1: Generate and Upload the Mission

Open a third terminal, navigate to your project directory, and run the mission generator script with the --upload flag:

python mission_generator.py --upload

This will create a file named mission.txt and then immediately try to upload this mission to the running SITL instance. You should see "Mission upload successful!" in the terminal.

Step 2: Start the Mission in SITL

Go back to the PX4 SITL terminal (the one with the pxh> prompt) and type the following command to start the mission you just uploaded:

# In the PX4 SITL console (pxh>)
mission start

The drone will now arm, take off, and fly the square pattern. You can watch its progress in real-time on your ground station map!

(Optional) Manual Mission Loading:
If you prefer to load the mission manually, you can still run python mission_generator.py (without --upload) to generate the mission.txt file. Then, use the following command in the SITL console, providing the full path to the file:

# In the PX4 SITL console (pxh>)
mission load /path/to/your/project/mission.txt
mission start
