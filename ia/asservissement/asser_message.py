from enum import Enum

class AsservMessage(Enum):
    # No param messages
    emergency_stop=10
    emergency_stop_reset=11
    normal_speed_acc_mode=15
    slow_speed_acc_mode=16
    # Two param messages
    max_motor_speed=17 # Only one param mandatory here, but add a dummy ID one
    turn=20
    straight=21
    # Three param messages
    face=22
    goto_front=23
    goto_back=24
    goto_nostop=25
    set_position=26
    # Four param messages
    orbital_turn=30