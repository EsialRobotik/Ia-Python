import logging


class RobotFilter(logging.Filter):
    def __init__(self, who: str) -> None:
        super().__init__()
        self.who = who

    def filter(self, record: logging.LogRecord) -> bool:
        record.who = self.who
        return True