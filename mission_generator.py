import argparse
from pymavlink import mavutil

def generate_mission():
    mission_items = []

    # Takeoff
    mission_items.append({
        "seq": 0,
        "frame": mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        "command": mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        "current": 1,
        "autocontinue": 1,
        "param1": 0, "param2": 0, "param3": 0, "param4": 0,
        "x": 47.3980399, "y": 8.5455725, "z": 10
    })
    print("Added Takeoff command")

    # Waypoints
    waypoints = [
        (47.398742, 8.545594, 10),
        (47.398742, 8.546594, 10),
        (47.397742, 8.546594, 10)
    ]
    for i, (lat, lon, alt) in enumerate(waypoints, start=1):
        mission_items.append({
            "seq": i,
            "frame": mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            "command": mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            "current": 0,
            "autocontinue": 1,
            "param1": 0, "param2": 0, "param3": 0, "param4": 0,
            "x": lat, "y": lon, "z": alt
        })
        print(f"Added Waypoint {i}: {lat}, {lon}")

    return mission_items


def upload_mission(mission_items, connection_str):
    # Connect to vehicle
    master = mavutil.mavlink_connection(connection_str)
    master.wait_heartbeat()
    print("Heartbeat from system (system %u component %u)" % (master.target_system, master.target_component))

    # Clear existing mission
    master.mav.mission_clear_all_send(master.target_system, master.target_component)
    ack = master.recv_match(type=['MISSION_ACK'], blocking=True)
    print(f"Received MISSION_ACK: {ack}")

    # Upload new mission
    master.mav.mission_count_send(master.target_system, master.target_component, len(mission_items))

    for item in mission_items:
        msg = master.recv_match(type=['MISSION_REQUEST_INT'], blocking=True)
        seq = msg.seq
        mission = mission_items[seq]
        master.mav.mission_item_int_send(
            master.target_system,
            master.target_component,
            mission["seq"],
            mission["frame"],
            mission["command"],
            mission["current"],
            mission["autocontinue"],
            mission["param1"], mission["param2"], mission["param3"], mission["param4"],
            int(mission["x"] * 1e7),
            int(mission["y"] * 1e7),
            mission["z"]
        )
        print(f"Vehicle requests waypoint {seq}. Sent.")

    ack = master.recv_match(type=['MISSION_ACK'], blocking=True)
    print(f"Final ACK: {ack}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", action="store_true", help="Upload mission to vehicle")
    parser.add_argument("--connect", default="udp:127.0.0.1:14550", help="Connection string")
    args = parser.parse_args()

    mission = generate_mission()
    print(f"\nMission successfully created with {len(mission)} items.")

    if args.upload:
        upload_mission(mission, args.connect)
