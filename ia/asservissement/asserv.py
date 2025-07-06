import logging

from ia.asservissement.asserv_status import AsservStatus
from ia.asservissement.movement_direction import MovementDirection
from ia.utils.position import Position

logger = logging.getLogger(__name__)

import serial
import threading
import time

class Asserv:
    """
    The Asserv class provides an interface to control a robot's movement and position using a serial connection.
    Attributes:
        serial_port (str): The serial port to which the robot is connected.
        baud_rate (int): The baud rate for the serial communication.
        serial (serial.Serial): The serial connection object.
        position (position): The current position of the robot.
        direction (movement_direction): The current movement direction of the robot.
        status_countdown (int): Countdown for the status of the robot.
        asserv_status (asserv_status): The current status of the robot.
        queue_size (int): The size of the command queue.
        gostart_config (dict): Configuration for the go start sequence.
        lock (threading.Lock): A lock to ensure thread safety.
        read_thread (threading.Thread): A thread to read and parse the robot's position.
    Methods:
        initialize(): Initializes the robot.
        stop(): Stops the robot.
        emergency_stop(): Performs an emergency stop.
        emergency_reset(): Resets the robot after an emergency stop.
        go(dist): Moves the robot forward or backward by a specified distance.
        turn(degree): Turns the robot by a specified degree.
        go_to(position): Moves the robot to a specified position.
        go_to_chain(position): Moves the robot to a specified position in a chain of movements.
        go_to_reverse(position): Moves the robot to a specified position in reverse.
        face(position): Faces the robot towards a specified position.
        set_odometrie(x, y, theta): Sets the odometry of the robot.
        enable_low_speed(enable): Enables or disables low speed mode.
        set_speed(pct): Sets the speed of the robot as a percentage.
        set_speed_callage(pct): Sets the speed of the robot for callage.
        enable_regulator_angle(enable): Enables or disables the angle regulator.
        reset_regulator_angle(): Resets the angle regulator.
        enable_regulator_distance(enable): Enables or disables the distance regulator.
        reset_regulator_distance(): Resets the distance regulator.
        enable_motors(enable): Enables or disables the motors.
        parse_asserv_position(str): Parses the position data from the robot.
        wait_for_asserv(): Waits for the robot to finish its current command.
        wait_for_halted_or_blocked(timeout_ms): Waits for the robot to be halted or blocked within a timeout.
        go_start(is_color0): Executes the go start sequence based on the color configuration.
    """

    def __init__(self, serial_port: str, baud_rate: int, gostart_config: dict) -> None:
        """
        Initializes the Asserv object with the given serial port, baud rate, and gostart configuration.
        Args:
            serial_port (str): The serial port to be used for communication.
            baud_rate (int): The baud rate for the serial communication.
            gostart_config (dict): Configuration settings for the gostart.
        Attributes:
            serial_port (str): The serial port to be used for communication.
            baud_rate (int): The baud rate for the serial communication.
            serial (serial.Serial): The serial communication object.
            position (position): The current position of the robot.
            direction (None): The current direction of the robot (initially None).
            status_countdown (int): Countdown for the status (initially 0).
            asserv_status (asserv_status): The current status of the asservissement (initially STATUS_IDLE).
            queue_size (int): The size of the command queue (initially 0).
            gostart_config (dict): Configuration settings for the gostart.
            lock (threading.Lock): A lock for thread-safe operations.
            read_thread (threading.Thread): A thread for reading and parsing the asservissement position.
        """

        self.serial_port = serial_port
        self.baud_rate = baud_rate
        logger.info(f"Creating Asserv object with serial port {serial_port} and baud rate {baud_rate}.")
        self.serial = serial.Serial(
            port=serial_port,
            baudrate=baud_rate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        self.position = Position(0, 0)
        self.last_log = ''
        self.direction = None
        self.status_countdown = 0
        self.asserv_status = AsservStatus.STATUS_IDLE
        self.queue_size = 0
        self.gostart_config = gostart_config
        self.reading_buffer = []
        self.lock = threading.Lock()
        self.read_thread = threading.Thread(target=self.parse_asserv_position)
        self.read_thread.daemon = True
        self.read_thread.start()

    def initialize(self) -> None:
        """
        Initializes the Asserv system by sending an initialization command
        to the serial interface and logging the initialization process.
        This method writes the byte "I" to the serial interface to signal
        the start of the initialization process and logs the action using
        the logger.
        """

        logger.info("init")
        self.serial.write(f"I\n".encode())

    def stop(self) -> None:
        """
        Stops the robot by sending the stop command "M0" to the serial interface.
        This method logs the stop action and writes the stop command to the serial port
        to halt the robot's movement.
        """

        logger.info("stop")
        self.serial.write(f"M0\n".encode())

    def emergency_stop(self) -> None:
        """
        Immediately halts the robot's movement and updates its status.
        This method performs the following actions:
        - Logs an "emergencyStop" message.
        - Sets the robot's status to `STATUS_HALTED`.
        - Sends a halt command ("h") to the robot's serial interface.
        - Sets the movement direction to `NONE`.
        This method is typically used in emergency situations where the robot needs to stop all operations immediately.
        """

        logger.info("emergencyStop")
        self.asserv_status = AsservStatus.STATUS_HALTED
        self.serial.write(f"h\n".encode())
        self.direction = MovementDirection.NONE

    def emergency_reset(self) -> None:
        """
        Resets the system to an idle state in case of an emergency.
        This method logs an emergency reset event, sets the asserv_status to 
        STATUS_IDLE, and sends a reset command ('r') via the serial interface.
        """

        logger.info("emergencyReset")
        self.asserv_status = AsservStatus.STATUS_IDLE
        self.serial.write(f"r\n".encode())

    def go(self, dist: int) -> None:
        """
        Initiates movement of the robot for a specified distance.
        Args:
            dist (float): The distance to move. Positive values indicate forward movement,
                          while negative values indicate backward movement.
        Raises:
            None
        Side Effects:
            - Logs the movement command.
            - Updates the asserv_status to STATUS_RUNNING.
            - Sets the status_countdown to 2 within a thread-safe block.
            - Sets the movement direction based on the distance.
            - Sends the movement command to the serial interface.
        """

        logger.info(f"go : {dist}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.FORWARD if dist > 0 else MovementDirection.BACKWARD
        self.serial.write(f"v{dist}\n".encode())

    def turn(self, degree: int) -> None:
        """
        Rotates the robot by a specified degree.
        Args:
            degree (int): The degree to turn the robot. Positive values indicate a clockwise turn, 
                  while negative values indicate a counterclockwise turn.
        Logs:
            Logs the turn action with the specified degree.
        Updates:
            - Sets the asserv_status to STATUS_RUNNING.
            - Sets the status_countdown to 2 within a thread-safe block.
            - Sets the direction to MovementDirection.NONE.
            - Sends the turn command to the robot's serial interface.
        """

        logger.info(f"turn : {degree}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.NONE
        self.serial.write(f"t{degree}\n".encode())

    def go_to(self, position: Position) -> None:
        """
        Moves the robot to the specified position.
        Args:
            position (position): The target position to move to, containing x and y coordinates.
        Logs:
            Logs the target position using the logger.
        Updates:
            - Sets the asserv_status to STATUS_RUNNING.
            - Sets the status_countdown to 2 within a thread-safe block.
            - Sets the movement direction to FORWARD.
            - Sends the target position to the robot via serial communication.
        """

        logger.info(f"goTo : {position}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.FORWARD
        self.serial.write(f"g{position.x}#{position.y}\n".encode())

    def go_to_chain(self, position: Position) -> None:
        """
        Moves the robot to the specified position and a chain of movements.
        Args:
            position (position): The target position to move to, containing x and y coordinates.
        Logs:
            Logs the target position using the logger.
        Side Effects:
            - Sets the asserv_status to STATUS_RUNNING.
            - Sets the status_countdown to 2 within a thread-safe block.
            - Sets the movement direction to FORWARD.
            - Sends the target position to the serial interface in the format "e{x}#{y}".
        """

        logger.info(f"goToChain : {position}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.FORWARD
        self.serial.write(f"e{position.x}#{position.y}\n".encode())

    def go_to_reverse(self, position: Position) -> None:
        """
        Initiates a reverse movement to the specified position.
        Args:
            position (position): The target position to move to in reverse. 
                                 It should have 'x' and 'y' attributes representing coordinates.
        Logs:
            Logs the action with the target position.
        Updates:
            - Sets the asserv_status to STATUS_RUNNING.
            - Sets the status_countdown to 2 within a thread-safe block.
            - Sets the movement direction to BACKWARD.
            - Sends the target position to the serial interface in the format "b{x}#{y}".
        """

        logger.info(f"goToReverse : {position}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.BACKWARD
        self.serial.write(f"b{position.x}#{position.y}\n".encode())

    def face(self, position: Position) -> None:
        """
        Directs the robot to face a given position.
        Args:
            position (position): The target position with x and y coordinates.
        Raises:
            Exception: If there is an issue with serial communication.
        Logs:
            Logs the target position using the logger.
        """

        logger.info(f"goToFace : {position}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.NONE
        self.serial.write(f"f{position.x}#{position.y}\n".encode())

    def set_odometrie(self, x: int, y: int, theta: float) -> None:
        """
        Sets the odometry values for the robot.
        Parameters:
        x (float): The x-coordinate of the robot's position.
        y (float): The y-coordinate of the robot's position.
        theta (float): The orientation angle of the robot in radians.
        Returns:
        None
        """

        logger.info(f"setOdometrie P{x}#{y}#{theta}")
        self.serial.write(f"P{x}#{y}#{theta}\n".encode())

    def enable_low_speed(self, enable: bool) -> None:
        """
        Enables or disables low speed mode for the robot.
        Parameters:
        enable (bool): If True, low speed mode is enabled. If False, low speed mode is disabled.
        Returns:
        None
        """

        logger.info(f"enableLowSpeed : {enable}")
        self.serial.write(f"n\n".encode() if enable else f"N\n".encode())

    def set_speed(self, pct: int) -> None:
        """
        Set the speed of the robot.
        This method sets the speed of the robot to the specified percentage.
        It also enables or disables low speed mode based on whether the 
        percentage is 100 or not.
        Args:
            pct (int): The speed percentage to set. Should be between 0 and 100.
        Returns:
            None
        """

        logger.info(f"setSpeed {pct}%")
        self.enable_low_speed(pct != 100)

    def set_speed_callage(self, pct: int) -> None:
        """
        Set the speed of the robot by sending a command to the serial interface.
        Parameters:
        pct (int): The speed percentage to set. This should be an integer value representing the desired speed as a percentage.
        Returns:
        None
        """

        logger.info(f"setSpeed {pct}%")
        self.serial.write(f"S{pct}\n".encode())

    def enable_regulator_angle(self, enable: bool) -> None:
        """
        Enables or disables the angle regulator.
        This method sends a command to the serial interface to enable or disable
        the angle regulator based on the provided boolean value.
        Args:
            enable (bool): If True, enables the angle regulator. If False, disables it.
        Returns:
            None
        """

        logger.info(f"enableRegulatorAngle : {enable}")
        self.serial.write(f"Rae\n".encode() if enable else f"Rad\n".encode())

    def reset_regulator_angle(self) -> None:
        """
        Resets the regulator angle by sending a specific command to the serial interface.
        This method logs the action and writes the command "Rar" to the serial interface
        to reset the regulator angle.
        Raises:
            SerialException: If there is an error writing to the serial interface.
        """

        logger.info("resetRegulatorAngle")
        self.serial.write(f"Rar\n".encode())

    def enable_regulator_distance(self, enable: bool) -> None:
        """
        Enable or disable the distance regulator.
        This method sends a command to the serial interface to enable or disable
        the distance regulator based on the provided boolean value.
        Args:
            enable (bool): If True, the distance regulator is enabled. If False, it is disabled.
        Returns:
            None
        """

        logger.info(f"enableRegulatorDistance : {enable}")
        self.serial.write(f"Rde\n".encode() if enable else f"Rdd\n".encode())

    def reset_regulator_distance(self) -> None:
        """
        Resets the distance regulator by sending a reset command to the serial interface.
        This method logs the reset action and writes the reset command "Rdr" to the serial port.
        """

        logger.info("resetRegulatorDistance")
        self.serial.write(f"Rdr\n".encode())

    def enable_motors(self, enable: bool) -> None:
        """
        Enable or disable the motors.
        This method sends a command to the motor controller to enable or disable the motors.
        It logs the action and writes the appropriate command to the serial interface.
        Args:
            enable (bool): If True, the motors will be enabled. If False, the motors will be disabled.
        """

        logger.info(f"enable motors {enable}")
        self.serial.write(f"M{1 if enable else 0}\n".encode())

    def parse_asserv_position(self) -> None:
        """
        Parses a string containing asservissement position data and updates the object's attributes accordingly.
        The input string is expected to have the following format:
        "#x;y;theta;asserv_status;queue_size"
        where:
        - x: integer representing the x-coordinate of the position.
        - y: integer representing the y-coordinate of the position.
        - theta: float representing the orientation angle.
        - asserv_status: integer representing the status of the asservissement system.
        - queue_size: integer representing the size of the queue.
        The method updates the following attributes of the object:
        - self.position.x
        - self.position.y
        - self.position.theta
        - self.asserv_status
        - self.queue_size
        The asserv_status is mapped to the following states:
        - 0: STATUS_IDLE
        - 1: STATUS_RUNNING
        - 2: STATUS_HALTED
        - 3: STATUS_BLOCKED
        If the asserv_status is 0, the status_countdown is decremented and if it reaches 0, the asserv_status is set to STATUS_IDLE.
        Args:
            str (str): The input string containing the asservissement position data.
        Raises:
            Exception: If the input string is not parsable, an exception is caught and a log message is generated.
        """

        while True:
            try:
                str = self.serial.readline().decode().strip()
                self.last_log = str
                logger.debug(f"Position : {str}")
                if str.startswith("#"):
                    str = str[1:]
                    if "#" in str:
                        continue
                    data = str.split(";")

                    self.position.x = int(data[0])
                    self.position.y = int(data[1])
                    self.position.theta = float(data[2])
                    asserv_status_int = int(data[3])
                    if asserv_status_int == 0:
                        with self.lock:
                            self.status_countdown -= 1
                            if self.status_countdown <= 0:
                                self.asserv_status = AsservStatus.STATUS_IDLE
                    elif asserv_status_int == 1:
                        self.asserv_status = AsservStatus.STATUS_RUNNING
                    elif asserv_status_int == 2:
                        self.asserv_status = AsservStatus.STATUS_HALTED
                    elif asserv_status_int == 3:
                        self.asserv_status = AsservStatus.STATUS_BLOCKED
                    self.queue_size = int(data[4])
            except Exception as e:
                logger.error("Trace asservissement non parsable")

    def wait_for_asserv(self) -> None:
        """
        Waits for the asservissement process to complete.
        This method continuously checks the status of the asservissement process
        and waits until the queue is empty and the asservissement status is idle. It
        pauses for 5 milliseconds between each check to avoid busy-waiting.
        Returns:
            None
        """

        while not (self.queue_size == 0 and self.asserv_status == AsservStatus.STATUS_IDLE):
            time.sleep(0.005)

    def wait_for_halted_or_blocked(self, timeout_ms: int) -> None:
        """
        Waits for the asservissement system to halt or become blocked within a specified timeout.
        Args:
            timeout_ms (int): The maximum time to wait in milliseconds.
        Returns:
            None
        """

        start_time = time.time_ns()
        while self.asserv_status == AsservStatus.STATUS_RUNNING and ((time.time_ns() - start_time)  / 1000000) < timeout_ms:
            time.sleep(0.01)

    def go_start(self, color: str) -> None:
        """
        Executes a series of movement instructions to start the robot.
        Parameters:
        color (str): Determines the starting configuration based on color
        The method processes a list of instructions, where each instruction is a dictionary 
        containing the type of movement and associated parameters. The supported instruction 
        types are:
        - "go": Move forward a specified distance.
        - "go_timed": Move forward a specified distance with a time limit.
        - "turn": Turn by a specified distance.
        - "goto": Move to a specified (x, y) position.
        - "goto_back": Move to a specified (x, y) position in reverse.
        - "face": Face towards a specified (x, y) position.
        - "angle": Enable or disable the angle regulator.
        - "distance": Enable or disable the distance regulator.
        - "set_x": Set the odometry X value.
        - "set_y": Set the odometry Y value.
        - "speed": Set the movement speed.
        Raises:
        Exception: If an unknown instruction type is encountered.
        The method also logs each instruction and its execution status.
        """

        start = self.gostart_config[color]
        time.sleep(0.15)
        for instruction in start:
            temp = instruction
            logger.debug(temp)
            if temp["type"] == "go":
                self.go(temp["dist"])
                logger.info(f"Go {temp['dist']}")
            elif temp["type"] == "go_timed":
                logger.info(f"Go timed {temp['dist']}")
                self.go(temp["dist"])
                time.sleep(0.11)  # Wait a bit to ensure the asservissement has received the command
                self.wait_for_halted_or_blocked(500)
                self.emergency_stop()
                time.sleep(2)
                self.emergency_reset()
                logger.info(f"Go timed end {temp['dist']}")
            elif temp["type"] == "turn":
                self.turn(temp["dist"])
                logger.info(f"Turn {temp['dist']}")
            elif temp["type"] == "goto":
                depart = Position(temp["x"], temp["y"])
                logger.info(f"Goto {depart}")
                self.go_to(depart)
            elif temp["type"] == "goto_back":
                depart = Position(temp["x"], temp["y"])
                logger.info(f"Goto {depart}")
                self.go_to_reverse(depart)
            elif temp["type"] == "face":
                alignement = Position(temp["x"], temp["y"])
                logger.info(f"Goto {alignement}")
                self.face(alignement)
            elif temp["type"] == "angle":
                logger.info(f"Enable regulator angle {temp['enable']}")
                self.enable_regulator_angle(temp["enable"])
            elif temp["type"] == "distance":
                logger.info(f"Enable regulator distance {temp['enable']}")
                self.enable_regulator_distance(temp["enable"])
            elif temp["type"] == "set_x":
                logger.info(f"Set odometrie X : {temp['value']}")
                self.set_odometrie(temp["value"], self.position.y, temp["theta"])
            elif temp["type"] == "set_y":
                logger.info(f"Set odometrie Y : {temp['value']}")
                self.set_odometrie(self.position.x, temp["value"], temp["theta"])
            elif temp["type"] == "speed":
                logger.info(f"Set speed {temp['value']}")
                self.set_speed_callage(temp["value"])
            else:
                raise Exception(f"Unknown instruction {temp}")
            self.wait_for_asserv()
        time.sleep(0.15)
        logger.info("goStart finished")