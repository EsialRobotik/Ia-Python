from ia.utils.position import Position


class AbstractTask:
    def __init__(self, desc=None, position_x=0, position_y=0, dist=0, task_type=None, subtype=None, action_id=None, mirror=None, timeout=-1, item_id=None):
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
        self.skip_flag = None
        self.needed_flag = None
        self.path_finding = None
        self.end_point = None

    def execute(self, start_point: Position):
        return ""

    def calculate_theta(self, current_position, final_x, final_y):
        if final_y == current_position.y:
            return 0 if final_x > current_position.x else 3.141592653589793
        elif final_x == current_position.x:
            return 1.5707963267948966 if final_y > current_position.y else -1.5707963267948966
        else:
            adjust = 0
            if final_y > current_position.y and final_x > current_position.x:
                adjust = 0
            elif final_y > current_position.y or final_x < current_position.x:
                adjust = 3.141592653589793
            return adjust + (final_y - current_position.y) / (final_x - current_position.x)

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
                "skip_flag": self.skip_flag,
                "needed_flag": self.needed_flag
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
            f"skip_flag={self.skip_flag}, "
            f"needed_flag={self.needed_flag}"
            f"}}"
        )

    def set_skip_flag(self, skip_flag):
        self.skip_flag = skip_flag
        return self

    def set_needed_flag(self, needed_flag):
        self.needed_flag = needed_flag
        return self