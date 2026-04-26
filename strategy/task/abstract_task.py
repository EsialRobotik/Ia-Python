import math

from ia.utils.position import Position


class AbstractTask:
    def __init__(self, desc=None, position_x=0, position_y=0, dist=0, task_type=None, subtype=None, action_id=None, mirror=None, timeout=-1, item_id=None, reset_flags=None, forward=None, turn_right=None):
        self.desc = desc
        self.position_x = position_x
        self.position_y = position_y
        self.dist = dist
        self.type = task_type
        self.subtype = subtype
        self.action_id = action_id
        self.mirror = mirror
        self.timeout = timeout
        self.item_id = item_id
        self.reset_flags = reset_flags
        self.forward = forward
        self.turn_right = turn_right
        self.needed_flag = None
        self.path_finding = None
        self.end_point = None

    def execute(self, start_point: Position):
        return ""

    def calculate_theta(self, current_position, final_x, final_y):
            return math.atan2(final_y - current_position.y, final_x - current_position.x)

    def to_dict(self):
            return {
                "desc": self.desc,
                "position_x": self.position_x,
                "position_y": self.position_y,
                "dist": self.dist,
                "type": self.type.value,
                "subtype": self.subtype.value,
                "action_id": self.action_id,
                "mirror": self.mirror.value,
                "timeout": self.timeout,
                "item_id": self.item_id,
                "reset_flags": self.reset_flags,
                "forward": self.forward,
                "turn_right": self.turn_right,
                "needed_flag": self.needed_flag,
            }

    def __str__(self):
        return (
            f"\n\t\t\t\t{self.__class__.__name__}{{"
            f"desc='{self.desc}', "
            f"position_x={self.position_x}, "
            f"position_y={self.position_y}, "
            f"dist={self.dist}, "
            f"type={self.type}, "
            f"subtype={self.subtype}, "
            f"action_id={self.action_id}, "
            f"item_id={self.item_id}, "
            f"needed_flag={self.needed_flag}"
            f"}}"
        )

    def set_needed_flag(self, needed_flag):
        self.needed_flag = needed_flag
        return self