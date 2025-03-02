class ActuatorCommand:
    def __init__(self, command: str, isasync: bool, timeout: float):
        self.command = command
        self.isasync = isasync
        self.timeout = timeout