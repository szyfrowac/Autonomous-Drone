# mission_generator.py
# This script can generate a new MAVLink mission or load an existing one
# from either a modern JSON (.plan) file or a legacy text (.txt) file
# and upload it to a PX4 SITL instance.

import time
import argparse
import json
from pymavlink import mavutil

def generate_mission_items():
    """
    Generates a list of mission waypoints as dictionaries for a simple square pattern.
    """
    mission_items = []
    home_lat, home_lon = 47.397742, 8.545594
    mission_alt = 20.0

    # 1. Takeoff command
    mission_items.append({
        "seq": 0, "frame": mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        "command": mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, "current": 1, "autocontinue": 1,
        "param1": 15, "param2": 0, "param3": 0, "param4": 0,
        "x": home_lat, "y": home_lon, "z": mission_alt
    })
    print("Added Takeoff command")

    # 2. Waypoint commands
    waypoints = [
        (47.398742, 8.545594), # North
        (47.398742, 8.546594), # North-East
        (47.397742, 8.546594), # South-East
    ]
    for i, (lat, lon) in enumerate(waypoints, start=1):
        mission_items.append({
            "seq": i, "frame": mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            "command": mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, "current": 0, "autocontinue": 1,
            "param1": 0, "param2": 0, "param3": 0, "param4": 0,
            "x": lat, "y": lon, "z": mission_alt
        })
        print(f"Added Waypoint {i}: {lat}, {lon}")

    # 3. RTL command
    mission_items.append({
        "seq": len(mission_items), "frame": mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        "command": mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH, "current": 0, "autocontinue": 1,
        "param1": 0, "param2": 0, "param3": 0, "param4": 0,
        "x": 0, "y": 0, "z": 0
    })
    print("Added Return-to-Launch command")
    return mission_items

def parse_plan_file(filename):
    """Parses a QGroundControl JSON .plan file."""
    mission_items = []
    try:
        with open(filename, 'r') as f:
            plan_data = json.load(f)

        # The actual mission items are in mission -> items
        raw_items = plan_data.get('mission', {}).get('items', [])
        seq_counter = 0

        for item in raw_items:
            # Helper function to safely process parameters
            def process_params(raw_params):
                # Ensure raw_params is a list
                if not isinstance(raw_params, list):
                    raw_params = [0, 0, 0, 0, 0, 0, 0]
                # Replace None with 0 for all params to avoid TypeErrors
                safe_params = [p if p is not None else 0 for p in raw_params]
                # Pad the list if it's too short, ensuring it has at least 7 elements
                while len(safe_params) < 7:
                    safe_params.append(0)
                return safe_params

            # Handle complex items like surveys by extracting their sub-items
            if item.get('type') == 'ComplexItem':
                for sub_item in item.get('TransectStyleComplexItem', {}).get('Items', []):
                    params = process_params(sub_item.get('params'))
                    mission_items.append({
                        "seq": seq_counter,
                        "frame": sub_item.get('frame', 3),
                        "command": sub_item.get('command', 16),
                        "current": 1 if seq_counter == 0 else 0,
                        "autocontinue": sub_item.get('autoContinue', True),
                        "param1": params[0], "param2": params[1], "param3": params[2], "param4": params[3],
                        "x": params[4], "y": params[5], "z": params[6]
                    })
                    seq_counter += 1
            # Handle simple items
            elif item.get('type') == 'SimpleItem':
                params = process_params(item.get('params'))
                mission_items.append({
                    "seq": seq_counter,
                    "frame": item.get('frame', 3),
                    "command": item.get('command', 16),
                    "current": 1 if seq_counter == 0 else 0,
                    "autocontinue": item.get('autoContinue', True),
                    "param1": params[0], "param2": params[1], "param3": params[2], "param4": params[3],
                    "x": params[4], "y": params[5], "z": params[6]
                })
                seq_counter += 1
        
        # Correct the 'current' flag to only be on the very first item
        if mission_items:
            for i in range(len(mission_items)):
                mission_items[i]['current'] = 1 if i == 0 else 0
                mission_items[i]['seq'] = i # Re-sequence everything to be safe

        print(f"Successfully loaded {len(mission_items)} mission items from {filename}")
        return mission_items

    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{filename}'")
        return None
    except Exception as e:
        print(f"An error occurred while parsing the .plan file: {e}")
        return None


def parse_txt_file(filename):
    """Loads a mission from a legacy QGroundControl .txt file."""
    mission_items = []
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        if not lines[0].startswith('QGC WPL'):
            print("Error: Invalid mission file format. Missing QGC header.")
            return None
        
        for line in lines[1:]:
            if not line.strip() or line.startswith('#'): continue
            parts = line.strip().split('\t')
            if len(parts) != 12: continue
            
            p = [float(part) for part in parts]
            mission_items.append({
                "seq": int(p[0]), "frame": int(p[2]), "command": int(p[3]),
                "current": int(p[1]), "autocontinue": int(p[11]),
                "param1": p[4], "param2": p[5], "param3": p[6], "param4": p[7],
                "x": p[8], "y": p[9], "z": p[10]
            })
        print(f"Successfully loaded {len(mission_items)} mission items from {filename}")
        return mission_items
    except Exception as e:
        print(f"An error occurred while reading the mission file: {e}")
        return None

def load_mission_from_file(filename):
    """Detects file type and loads mission items accordingly."""
    if filename.lower().endswith('.plan'):
        return parse_plan_file(filename)
    elif filename.lower().endswith('.txt'):
        return parse_txt_file(filename)
    else:
        print(f"Error: Unknown mission file format for '{filename}'. Please use .plan or .txt")
        return None

def upload_mission(connection_string, items):
    """Connects to a vehicle and uploads a list of mission items."""
    if not items:
        print("No mission items to upload.")
        return

    print(f"\nConnecting to vehicle on: {connection_string}")
    master = mavutil.mavlink_connection(connection_string)
    master.wait_heartbeat()
    print(f"Heartbeat from system (system {master.target_system} component {master.target_component})")

    target_system = master.target_system
    target_component = master.target_component

    print("\nClearing any existing mission from vehicle...")
    master.mav.mission_clear_all_send(target_system, target_component)
    ack = master.recv_match(type='MISSION_ACK', blocking=True, timeout=3)
    if ack:
        print(f"Received MISSION_ACK: {mavutil.mavlink.enums['MAV_MISSION_RESULT'][ack.type].name}")
    else:
        print("Error: No MISSION_ACK received after clearing mission.")
        return

    time.sleep(1)

    print(f"\nStarting mission upload of {len(items)} items...")
    master.mav.mission_count_send(target_system, target_component, len(items))

    for item in items:
        msg = master.recv_match(type=['MISSION_REQUEST', 'MISSION_REQUEST_INT'], blocking=True, timeout=3)
        if not msg:
            print("Error: No MISSION_REQUEST received from vehicle. Aborting.")
            return

        seq = msg.seq
        if seq >= len(items):
            print(f"Error: Vehicle requested sequence {seq}, which is out of bounds.")
            continue
            
        print(f"Vehicle requests waypoint {seq}. Sending...")
        
        mission_item_to_send = items[seq]
        master.mav.mission_item_int_send(
            target_system, target_component,
            mission_item_to_send["seq"], mission_item_to_send["frame"],
            mission_item_to_send["command"], mission_item_to_send["current"],
            mission_item_to_send["autocontinue"],
            mission_item_to_send["param1"], mission_item_to_send["param2"],
            mission_item_to_send["param3"], mission_item_to_send["param4"],
            int(mission_item_to_send.get("x", 0) * 1e7),
            int(mission_item_to_send.get("y", 0) * 1e7),
            mission_item_to_send.get("z", 0)
        )

    final_ack = master.recv_match(type='MISSION_ACK', blocking=True, timeout=3)
    if final_ack and final_ack.type == mavutil.mavlink.MAV_MISSION_ACCEPTED:
        print("\nMission upload successful!")
    elif final_ack:
        print(f"\nMission upload failed with code: {mavutil.mavlink.enums['MAV_MISSION_RESULT'][final_ack.type].name}")
    else:
        print("\nMission upload failed: No final MISSION_ACK received.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate, load, and/or upload a MAVLink mission.")
    parser.add_argument("--upload", action="store_true", help="Upload the generated mission directly to the vehicle.")
    parser.add_argument("--connect", default="udp:127.0.0.1:14550", help="MAVLink connection string.")
    parser.add_argument("--load-file", type=str, help="Path to a mission file (.plan or .txt) to load and upload.")
    args = parser.parse_args()

    mission_to_upload = None

    if args.load_file:
        mission_to_upload = load_mission_from_file(args.load_file)
        if not mission_to_upload:
            # Error message is printed inside the load function, just exit.
            exit()
    else:
        generated_mission = generate_mission_items()
        print(f"\nMission successfully created with {len(generated_mission)} items.")
        
        if args.upload:
            mission_to_upload = generated_mission

    if mission_to_upload and (args.upload or args.load_file):
        try:
            upload_mission(args.connect, mission_to_upload)
        except Exception as e:
            print(f"\nAn error occurred during upload: {e}")

