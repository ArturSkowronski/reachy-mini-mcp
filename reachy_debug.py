from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

# Connects to the simulation running on localhost
with ReachyMini() as mini:
    print("Connected to simulation!")
    
    # Look up and tilt head
    print("Moving head...")
    mini.goto_target(
        head=create_head_pose(z=20, roll=10, mm=True, degrees=True),
        duration=1.0
    )

    # Wiggle antennas
    print("Wiggling antennas...")
    mini.goto_target(antennas=[0.6, -0.6], duration=0.3)
    mini.goto_target(antennas=[-0.6, 0.6], duration=0.3)
    
    # Reset to rest position
    mini.goto_target(
        head=create_head_pose(),
        antennas=[0, 0],
        duration=1.0
    )