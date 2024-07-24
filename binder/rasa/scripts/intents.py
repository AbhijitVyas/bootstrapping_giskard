from enum import Enum

class Intent(Enum):
    POURING = "pouring"
    CUTTING = "cut"
    SHAKING = "shake"
    PICKUP = "pick_up"
    PUTDOWN = "put_down"
    DROPPING = "drop"

